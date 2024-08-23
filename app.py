from flask import Flask, request, Response, render_template, redirect, url_for
import sys
import re
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import logging
import yfinance as yf
import json
from langdetect import detect, LangDetectException
from langcodes import Language
from datetime import datetime, timezone, timedelta
import os
app = Flask(__name__)

def load_settings():
    with open('settings.json', 'r') as f:
        return json.load(f)

settings = load_settings()
timezone_offset = settings.get("TIMEZONE_OFFSET", 2)  # Default to GMT+0 if not specified
GMT_PLUS_2 = timezone(timedelta(hours=timezone_offset))

def update_global_settings():
    global SEARCH_DEPTH, FALLBACK_TO_AI_CHAT, LOOP_UNTIL_SUCCESS, DOCUMENTS_DIR, MIN_SCORE_THRESHOLD, DOCS_LOGS, important_phrases, stock_name_to_symbol, document_terms, stock_terms, language_to_country_code, language_to_output_format, transport_triggers, API_KEY

    SEARCH_DEPTH = settings.get("SEARCH_DEPTH", 40)
    FALLBACK_TO_AI_CHAT = settings.get("FALLBACK_TO_AI_CHAT", True)
    LOOP_UNTIL_SUCCESS = settings.get("LOOP_UNTIL_SUCCESS", False)
    DOCUMENTS_DIR = settings.get("DOCUMENTS_DIR", "/app/Documents")
    MIN_SCORE_THRESHOLD = settings.get("MIN_SCORE_THRESHOLD", 8)
    DOCS_LOGS = settings.get("DOCS_LOGS", True)
    important_phrases = settings.get("important_phrases", [])
    stock_name_to_symbol = settings.get("stock_name_to_symbol", {})
    document_terms = settings.get("document_terms", {})
    stock_terms = settings.get("stock_terms", {})
    language_to_country_code = settings.get("language_to_country_code", {})
    language_to_output_format = settings.get("language_to_output_format", {})
    transport_triggers = settings.get("transport_triggers", ['buss', 'tåg', 'flyg', 'station', 'resa', 'avfärd', 'ankomst', 'rutt', 'tidtabell'])
    API_KEY = settings.get("TRANSPORT_API_KEY", "YOUR_API_KEY_HERE")

update_global_settings()

# Logging setup based on settings
logging.basicConfig(level=logging.INFO)
docs_logger = logging.getLogger('docs_logs')
docs_logger.setLevel(logging.INFO)
docs_log_handler = logging.StreamHandler()
docs_logger.addHandler(docs_log_handler)

def parse_query(query):
    query = query.lower().strip()
    from_pattern = re.compile(r'från\s+([\w\s]+)\s+till\s+([\w\s]+)')
    to_pattern = re.compile(r'till\s+([\w\s]+)\s+från\s+([\w\s]+)')

    match_from_to = from_pattern.search(query)
    match_to_from = to_pattern.search(query)

    if match_from_to:
        origin = match_from_to.group(1).strip()
        destination = match_from_to.group(2).strip()
    elif match_to_from:
        destination = match_to_from.group(1).strip()
        origin = match_to_from.group(2).strip()
    else:
        raise ValueError("Kunde inte tolka frågan. Använd formatet 'När går bussen från [Start] till [Slut]?' eller 'När går bussen till [Slut] från [Start]?'")
    
    return origin, destination

def get_stop_id(stop_name):
    url = f"https://api.resrobot.se/v2.1/location.name?input={stop_name}&format=json&accessId={API_KEY}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return f"Fel: Mottog statuskod {response.status_code} från API."
    
    try:
        data = response.json()
    except ValueError:
        return "Fel: Kunde inte tolka JSON-svaret."
    
    stop_locations = [item['StopLocation'] for item in data['stopLocationOrCoordLocation'] if 'StopLocation' in item]
    
    if len(stop_locations) == 0:
        return f"Fel: Inga hållplatser hittades för {stop_name}."
    
    stop_id = stop_locations[0]['extId']
    return stop_id

def get_next_route(origin_id, dest_id):
    url = f"https://api.resrobot.se/v2.1/trip?format=json&originId={origin_id}&destId={dest_id}&passlist=0&showPassingPoints=0&numF=3&accessId={API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 400:
        return "Fel: Dålig förfrågan - Detta kan bero på en ogiltig kombination av hållplatser eller en inkompatibel rutt."
    elif response.status_code != 200:
        return f"Fel: Mottog statuskod {response.status_code} från API."
    
    try:
        data = response.json()
    except ValueError:
        return "Fel: Kunde inte tolka JSON-svaret."
    
    if 'Trip' not in data or len(data['Trip']) == 0:
        return "Fel: Inga resor hittades."
    
    return data['Trip']

def format_transport_response(trips):
    now = datetime.now(GMT_PLUS_2)
    formatted_response = f"Aktuell tid är {now.strftime('%H:%M')}.\n"
    
    for i, trip in enumerate(trips):
        origin = trip['LegList']['Leg'][0]['Origin']
        destination = trip['LegList']['Leg'][0]['Destination']
        product = trip['LegList']['Leg'][0]['Product'][0]
        
        dep_time = datetime.strptime(f"{origin['date']} {origin['time']}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone(GMT_PLUS_2)
        arr_time = datetime.strptime(f"{destination['date']} {destination['time']}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone(GMT_PLUS_2)
        
        minutes_to_departure = int((dep_time - now).total_seconds() / 60)
        day = dep_time.strftime("%A")
        bus_number = product['num']
        
        if i == 0:
            formatted_response += (
                f"Nästa resa från {origin['name']} till {destination['name']} med buss {bus_number} avgår om {minutes_to_departure} minuter "
                f"({dep_time.strftime('%H:%M')}) på {day} och anländer kl. {arr_time.strftime('%H:%M')}."
            )
        else:
            formatted_response += (
                f" Nästa avgång efter det med buss {bus_number} är om {minutes_to_departure} minuter ({dep_time.strftime('%H:%M')})."
            )

    return formatted_response

# Other functions
def detect_language(text):
    try:
        language_code = detect(text)
        language_name = Language.get(language_code).language_name().lower()
        return language_name
    except LangDetectException:
        return "english"

def check_for_stock_related_terms(user_input):
    language = detect_language(user_input)
    stock_term = stock_terms.get(language, stock_terms["english"])
    return stock_term.lower() in user_input.lower()

def check_for_document_related_terms(user_input):
    language = detect_language(user_input)
    document_term = document_terms.get(language, document_terms["english"])
    return document_term.lower() in user_input.lower()

def clean_query(query, language):
    document_term = document_terms.get(language, document_terms["english"])
    cleaned_query = re.sub(rf'\b{document_term}\b', '', query, flags=re.IGNORECASE).strip()
    return cleaned_query

def improved_string_matching(description, user_input):
    description = description.lower()
    user_input_words = user_input.lower().split()
    score = sum(2 if word in important_phrases else 1 for word in user_input_words if word in description)
    return score

def parse_description_for_answer(results, user_input):
    best_score = 0
    best_answer = None
    for result in results:
        description = result['body']
        score = improved_string_matching(description, user_input)
        if score > best_score:
            best_score = score
            best_answer = description
        if best_score >= MIN_SCORE_THRESHOLD:
            return best_answer
    return None

def inspect_page_source(url, user_input):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        for attempt in range(3):
            try:
                page = requests.get(url, headers=headers, timeout=10)
                page.raise_for_status()
                soup = BeautifulSoup(page.content, 'html.parser')
                json_ld = soup.find('script', type='application/ld+json')
                if json_ld:
                    structured_data = json_ld.get_text()
                    if improved_string_matching(structured_data, user_input):
                        return structured_data[:500]
                for tag in ['meta', 'div', 'span']:
                    elements = soup.find_all(tag)
                    for element in elements:
                        if element.get('content'):
                            content = element.get('content').lower()
                            if improved_string_matching(content, user_input):
                                return content[:500]
                text = soup.get_text().lower()
                if improved_string_matching(text, user_input):
                    return text[:500]
                break
            except requests.RequestException:
                continue
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
    return None

def fallback_to_ai_chat(user_input, data_block=None):
    try:
        ddg = DDGS()
        combined_input = f"{user_input}\n\nData Block:\n{data_block}" if data_block else user_input
        response = ddg.chat(combined_input, model="gpt-4o-mini")
        return response
    except Exception:
        return "I couldn't find the information directly, and the AI Chat also encountered an issue."

def ai_chat(user_input):
    query = user_input
    ddgs = DDGS()
    results = ddgs.text(query)
    if not results:
        return "No search results were found."
    attempt_count = 0
    while attempt_count < SEARCH_DEPTH or LOOP_UNTIL_SUCCESS:
        description_answer = parse_description_for_answer(results, user_input)
        if description_answer:
            return description_answer
        for index, result in enumerate(results[:SEARCH_DEPTH]):
            url = result['href']
            page_source_answer = inspect_page_source(url, user_input)
            if page_source_answer:
                return fallback_to_ai_chat(user_input, page_source_answer)
        attempt_count += 1
        results = ddgs.text(query)
    return fallback_to_ai_chat(user_input)

def get_stock_price(stock_name):
    symbol = stock_name_to_symbol.get(stock_name.lower())
    if not symbol:
        return {"error": "Stock symbol not found for the given stock name."}
    try:
        stock_info = yf.Ticker(symbol).info
        price = stock_info.get('regularMarketPrice')
        return {"symbol": symbol, "price": price}
    except Exception as e:
        logging.error(f"Error fetching stock price: {e}")
        return {"error": str(e)}

def format_output(symbol, price, language):
    if price is None:
        return "Price information not available."
    format_string = language_to_output_format.get(language, language_to_output_format["english"])
    return format_string.format(symbol=symbol, price=price)

def get_time():
    now = datetime.now()
    return now.strftime('%H:%M')

def get_current_tv_shows():
    tv_listing_url = "https://tv.nu/"  # Example URL
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    
    try:
        response = requests.get(tv_listing_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        show_elements = soup.find_all('div', class_='current-show')  # Example class name
        shows = []
        
        for show in show_elements:
            time = show.find('span', class_='time').text.strip()  # Adjust the class names as needed
            title = show.find('span', class_='title').text.strip()
            shows.append((time, title))
        
        return shows

    except requests.RequestException as e:
        logging.error(f"Error fetching TV listings: {e}")
        return []

def get_time():
    now = datetime.now(GMT_PLUS_2)
    return now.strftime('%H:%M')

# Web scraping functions
def scrape_website(url, query):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Example: Extracting text from <div> tags
        text = soup.get_text()
        return text[:2000]  # Limit to first 2000 characters for brevity
    except requests.RequestException as e:
        logging.error(f"Error scraping website: {e}")
        return None


def analyze_text(text, query):
    text = text.lower()
    query = query.lower()
    return query in text


def find_tv_schedule(query):
    search_engine = DDGS()
    search_results = search_engine.text(query)
    
    for result in search_results:
        url = result['href']
        page_text = scrape_website(url, query)
        if page_text and analyze_text(page_text, query):
            return page_text  # Return the first match for simplicity
    
    return None

def get_current_tv_shows():
    # Define a time range to check for current shows
    now = datetime.now(GMT_PLUS_2)
    current_time = now.strftime('%H:%M')
    
    # Example query to find current TV shows
    query = f"site:tv.nu vad spelas just nu på tv?"
    tv_data = find_tv_schedule(query)
    
    if not tv_data:
        return "No relevant TV schedule found."
    
    # Extract and format TV shows from the scraped data
    shows = []
    for line in tv_data.split('\n'):
        if current_time in line:  # Check if the current time is mentioned in the schedule
            shows.append(line)
    
    if not shows:
        shows.append("No shows starting at the exact current time, but here's the current schedule:")
    
    # Format response
    response = f"Current TV shows around {current_time}:\n"
    for show in shows:
        response += f"{show}\n"
    
    return response


@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    if request.method == 'POST':
        try:
            # Collect updated settings from the form submission
            new_settings = {
                "SEARCH_DEPTH": int(request.form['SEARCH_DEPTH']),
                "FALLBACK_TO_AI_CHAT": 'FALLBACK_TO_AI_CHAT' in request.form,
                "LOOP_UNTIL_SUCCESS": 'LOOP_UNTIL_SUCCESS' in request.form,
                "DOCUMENTS_DIR": request.form['DOCUMENTS_DIR'],
                "MIN_SCORE_THRESHOLD": int(request.form['MIN_SCORE_THRESHOLD']),
                "important_phrases": [phrase.strip() for phrase in request.form['important_phrases'].split(',')],
                "document_terms": dict(item.split(':') for item in request.form['document_terms'].strip().splitlines() if ':' in item),
                "stock_terms": dict(item.split(':') for item in request.form['stock_terms'].strip().splitlines() if ':' in item),
                "stock_name_to_symbol": dict(item.split(':') for item in request.form['stock_name_to_symbol'].strip().splitlines() if ':' in item),
                "language_to_country_code": dict(item.split(':') for item in request.form['language_to_country_code'].strip().splitlines() if ':' in item),
                "language_to_output_format": dict(item.split(':') for item in request.form['language_to_output_format'].strip().splitlines() if ':' in item),
                "PUBLIC_TRANSPORT_ENABLED": 'PUBLIC_TRANSPORT_ENABLED' in request.form,
                "TRANSPORT_API_KEY": request.form['TRANSPORT_API_KEY'],
                "DOCS_LOGS": 'DOCS_LOGS' in request.form
            }

            # Write the updated settings to the JSON file
            with open('settings.json', 'w') as f:
                json.dump(new_settings, f, indent=4)
                print("Settings saved to settings.json:", new_settings)  # Debug statement

            global settings
            settings = load_settings()  # Reload settings from the file
            update_global_settings()

            return redirect(url_for('settings_page'))

        except Exception as e:
            print("Error saving settings:", str(e))  # debug
            return render_template('settings.html', settings=settings, error=str(e))

    
    print("Loading settings for display:", settings)  # Debug statement
    return render_template('settings.html', settings=settings, api_key_placeholder="******")


@app.route('/reset_settings', methods=['POST'])
def reset_settings():
    try:
        default_settings = {
            "SEARCH_DEPTH": 40,
            "FALLBACK_TO_AI_CHAT": True,
            "LOOP_UNTIL_SUCCESS": False,
            "DOCUMENTS_DIR": "/app/Documents",
            "MIN_SCORE_THRESHOLD": 8,
            "important_phrases": [],
            "document_terms": {},
            "stock_terms": {},
            "stock_name_to_symbol": {},
            "language_to_country_code": {},
            "language_to_output_format": {},
            "PUBLIC_TRANSPORT_ENABLED": False,
            "TRANSPORT_API_KEY": "YOUR_API_KEY_HERE",
            "DOCS_LOGS": True
        }

        # Write the default settings to the JSON file
        with open('settings.json', 'w') as f:
            json.dump(default_settings, f, indent=4)
            print("Default settings written to settings.json")  # Debug statement

        # Update global settings in the application
        global settings
        settings = load_settings()  # Reload settings from the file
        update_global_settings()

        return redirect(url_for('settings_page'))

    except Exception as e:
        print("Error resetting settings:", str(e))  # Debug statement
        return redirect(url_for('settings_page', error=str(e)))



# Route to handle requests
@app.route('/', methods=['POST'])
def handle_request():
    data = request.json
    query = data.get('query', '')
    
    if any(trigger in query.lower() for trigger in transport_triggers):
        try:
            origin_stop, dest_stop = parse_query(query)
            origin_id = get_stop_id(origin_stop)
            dest_id = get_stop_id(dest_stop)
            
            if isinstance(origin_id, str) and "Fel" in origin_id:
                response = origin_id
            elif isinstance(dest_id, str) and "Fel" in dest_id:
                response = dest_id
            else:
                trips = get_next_route(origin_id, dest_id)
                if isinstance(trips, str) and "Fel" in trips:
                    response = trips
                else:
                    response = format_transport_response(trips)
        except ValueError as e:
            response = str(e)

    elif "tv" in query.lower() and "just nu" in query.lower():
        current_time = get_time()
        shows = get_current_tv_shows()
        response = f"Current TV shows at {current_time}:\n"
        for show in shows.split('\n'):
            response += f"{show}\n"
    
    elif check_for_document_related_terms(query):
        response = document_search(query)
    
    elif check_for_stock_related_terms(query):
        result = find_stock_info(query)
        if "error" in result:
            response = f"Error: {result['error']}"
        else:
            detected_language = detect_language(query)
            response = format_output(result["symbol"], result["price"], detected_language)
    
    else:
        response = ai_chat(query)
    
    return Response(response, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5556)
