from flask import Flask, request, Response, render_template, redirect, url_for
import sys
import re
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import logging
import yfinance as yf
from langdetect import detect, LangDetectException
from langcodes import Language
import argparse
import os

app = Flask(__name__)

# Initial settings
settings = {
    "SEARCH_DEPTH": 40,
    "FALLBACK_TO_AI_CHAT": True,
    "LOOP_UNTIL_SUCCESS": False,
    "DOCUMENTS_DIR": os.path.expanduser("~/Documents"),
    "MIN_SCORE_THRESHOLD": 8,
    "DOCS_LOGS": True,
    "important_phrases": [
        'stänger', 'öppettider', 'när', 'tid', 'datum', 'match', 'klockan', 'pris', 
        'väder', 'regn', 'idag', 'imorgon', 'björklöven', 'björklövens'
    ],
    "stock_name_to_symbol": {
        "apple": "AAPL",
        "volvo": "VOLV-B.ST",
        "volkswagen": "VOW3.DE",
        "l'oréal": "OR.PA",
        "equinor": "EQNR.OL",
        "asml": "ASML.AS",
    },
    "document_terms": {
        "english": "document",
        "swedish": "dokument",
        "german": "dokument",
        "french": "document",
        "spanish": "documento",
        "italian": "documento",
        "norwegian": "dokument",
        "dutch": "document",
    },
    "stock_terms": {
        "english": "stock",
        "swedish": "aktie",
        "german": "aktie",
        "french": "action",
        "spanish": "acción",
        "italian": "azione",
        "norwegian": "aksje",
        "dutch": "aandeel",
    },
    "language_to_country_code": {
        "swedish": ".ST",
        "english": "",
        "german": ".DE",
        "french": ".PA",
        "spanish": ".MC",
        "italian": ".MI",
        "norwegian": ".OL",
        "dutch": ".AS",
    },
    "language_to_output_format": {
        "swedish_kr": "Priset på en {symbol} aktie är: {price:.2f} kr",
        "swedish_dollar": "Priset på en {symbol} aktie är: {price:.2f} dollar",
        "english": "The current price of a {symbol} stock is ${price:.2f}.",
        "german": "Der aktuelle Preis einer {symbol} Aktie beträgt {price:.2f} €.",
        "french": "Le prix actuel d'une action {symbol} est de {price:.2f} €.",
        "spanish": "El precio actual de una acción de {symbol} es {price:.2f} €.",
        "italian": "Il prezzo attuale di un'azione {symbol} è {price:.2f} €.",
        "norwegian": "Prisen på en {symbol} aksje er {price:.2f} kr.",
        "dutch": "De huidige prijs van een {symbol} aandeel is {price:.2f} €.",
    }
}

# Update global settings
def update_global_settings():
    global SEARCH_DEPTH, FALLBACK_TO_AI_CHAT, LOOP_UNTIL_SUCCESS, DOCUMENTS_DIR, MIN_SCORE_THRESHOLD, DOCS_LOGS, important_phrases, stock_name_to_symbol, document_terms, stock_terms, language_to_country_code, language_to_output_format
    SEARCH_DEPTH = settings["SEARCH_DEPTH"]
    FALLBACK_TO_AI_CHAT = settings["FALLBACK_TO_AI_CHAT"]
    LOOP_UNTIL_SUCCESS = settings["LOOP_UNTIL_SUCCESS"]
    DOCUMENTS_DIR = settings["DOCUMENTS_DIR"]
    MIN_SCORE_THRESHOLD = settings["MIN_SCORE_THRESHOLD"]
    DOCS_LOGS = settings["DOCS_LOGS"]
    important_phrases = settings["important_phrases"]
    stock_name_to_symbol = settings["stock_name_to_symbol"]
    document_terms = settings["document_terms"]
    stock_terms = settings["stock_terms"]
    language_to_country_code = settings["language_to_country_code"]
    language_to_output_format = settings["language_to_output_format"]

update_global_settings()

logging.basicConfig(level=logging.INFO)
docs_logger = logging.getLogger('docs_logs')
docs_logger.setLevel(logging.INFO)
docs_log_handler = logging.StreamHandler()
docs_logger.addHandler(docs_log_handler)

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    if request.method == 'POST':
        # Handle form submission
        for key in settings.keys():
            if key in request.form:
                if key == "important_phrases":
                    settings[key] = request.form.getlist(key)
                elif isinstance(settings[key], bool):
                    settings[key] = request.form.get(key) == 'on'
                elif isinstance(settings[key], int):
                    settings[key] = int(request.form[key])
                elif isinstance(settings[key], str):
                    settings[key] = request.form[key]
        # Update global variables
        update_global_settings()
        return redirect(url_for('settings_page'))

    return render_template('settings.html', settings=settings)

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
        if not LOOP_UNTIL_SUCCESS:
            break
    if FALLBACK_TO_AI_CHAT:
        return fallback_to_ai_chat(user_input)
    else:
        return "I searched the web but couldn't find a clear answer to your question."

def get_stock_price(query):
    detected_language = detect_language(query)
    country_code = language_to_country_code.get(detected_language, "")
    for name, symbol in stock_name_to_symbol.items():
        if name.lower() in query.lower():
            try:
                return fetch_stock_data(symbol)
            except Exception as e:
                return {"error": str(e)}
    ddg = DDGS()
    results = ddg.chat(query + " stock symbol")
    if not results:
        return {"error": "No results found"}
    match = re.search(r'\b[A-Z0-9]{2,5}(?:-[A-Z])?\b', results)
    if match:
        symbol = match.group(0)
        try:
            if country_code and not symbol.endswith(country_code):
                symbol += country_code
            return fetch_stock_data(symbol)
        except Exception as e:
            return {"error": str(e)}
    return {"error": "Stock symbol not recognized"}

def fetch_stock_data(symbol):
    stock = yf.Ticker(symbol)
    history_data = stock.history(period='1mo')
    if not history_data.empty:
        price = history_data['Close'].iloc[-1]
        return {"symbol": symbol, "price": price}
    return {"error": f"No price data found for {symbol}. This stock may be delisted or not available."}

def format_output(symbol, price, language):
    if language == "swedish":
        output_format = language_to_output_format["swedish_kr"] if symbol.endswith(".ST") else language_to_output_format["swedish_dollar"]
    else:
        output_format = language_to_output_format.get(language, language_to_output_format["english"])
    return output_format.format(symbol=symbol, price=price)

def load_documents(doc_dir):
    documents = {}
    for root, _, files in os.walk(doc_dir):
        for file in files:
            if file.endswith(".txt"):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as file_obj:
                    documents[path] = file_obj.read()
    return documents

def search_documents(queries, documents):
    results = []
    for query in queries:
        query = query.lower()
        for path, text in documents.items():
            if DOCS_LOGS:
                docs_logger.info(f"Searching in file: {path}, with query: '{query}'")
            if query in text.lower():
                start = text.lower().index(query)
                snippet = text[max(0, start - 50):start + 500]
                results.append((path, snippet, query))
    return results

def format_path(path):
    parts = path.split('/')
    if len(parts) > 1:
        return f"/{parts[-2]}  / {parts[-1]}"
    return path

def document_search(query):
    language = detect_language(query)
    cleaned_query = clean_query(query, language)
    cleaned_query = cleaned_query.lower()
    if DOCS_LOGS:
        docs_logger.info(f"Starting document search in directory: {DOCUMENTS_DIR}")
    documents = load_documents(DOCUMENTS_DIR)
    results = search_documents([cleaned_query], documents)
    if results:
        for path, snippet, _ in results:
            formatted_path = format_path(path)
            return f"Your search for '{cleaned_query}' was found in: {formatted_path}\n{snippet}\n"
    else:
        return "No results found."

@app.route('/', methods=['POST'])
def handle_request():
    data = request.json
    query = data.get('query', '')
    
    if check_for_document_related_terms(query):
        response = document_search(query)
    elif check_for_stock_related_terms(query):
        result = get_stock_price(query)
        if "error" in result:
            response = f"Error: {result['error']}"
        else:
            detected_language = detect_language(query)
            response = format_output(result["symbol"], result["price"], detected_language)
    else:
        response = ai_chat(query)
    
    return Response(response, mimetype='text/plain')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5556)
