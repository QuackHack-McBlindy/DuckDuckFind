from flask import Flask, request, render_template, redirect, url_for, Response
import os
import logging
import yfinance as yf
import re
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from langdetect import detect, LangDetectException
from langcodes import Language

app = Flask(__name__)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### --> GLOBAL SETTINGS <-- ###
SEARCH_DEPTH = 40
FALLBACK_TO_AI_CHAT = True
LOOP_UNTIL_SUCCESS = False
DOCUMENTS_DIR = os.path.expanduser("~/Documents")
MIN_SCORE_THRESHOLD = 8
important_phrases = [
    'stänger', 'öppettider', 'när', 'tid', 'datum', 'match', 'klockan', 'pris', 
    'väder', 'regn', 'idag', 'imorgon', 'björklöven', 'björklövens'
]
DOCS_LOGS = True
stock_name_to_symbol = {
    "apple": "AAPL",
    "volvo": "VOLV-B.ST",
    "volkswagen": "VOW3.DE",
    "l'oréal": "OR.PA",
    "equinor": "EQNR.OL",
    "asml": "ASML.AS",
}
document_terms = {
    "english": "document",
    "swedish": "dokument",
    "german": "dokument",
    "french": "document",
    "spanish": "documento",
    "italian": "documento",
    "norwegian": "dokument",
    "dutch": "document",
}
stock_terms = {
    "english": "stock",
    "swedish": "aktie",
    "german": "aktie",
    "french": "action",
    "spanish": "acción",
    "italian": "azione",
    "norwegian": "aksje",
    "dutch": "aandeel",
}
language_to_country_code = {
    "swedish": ".ST",
    "english": "",
    "german": ".DE",
    "french": ".PA",
    "spanish": ".MC",
    "italian": ".MI",
    "norwegian": ".OL",
    "dutch": ".AS",
}
language_to_output_format = {
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
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

logging.basicConfig(level=logging.INFO)
docs_logger = logging.getLogger('docs_logs')
docs_logger.setLevel(logging.INFO)
docs_log_handler = logging.StreamHandler()
docs_logger.addHandler(docs_log_handler)

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
    price = stock.history(period="1d").iloc[-1]['Close']
    return {"symbol": symbol, "price": price}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form.get("user_input", "")
        if check_for_stock_related_terms(user_input):
            stock_price = get_stock_price(user_input)
            if "error" in stock_price:
                return render_template("index.html", result=stock_price["error"])
            detected_language = detect_language(user_input)
            output_format = language_to_output_format.get(detected_language, language_to_output_format["english"])
            result = output_format.format(symbol=stock_price["symbol"], price=stock_price["price"])
        elif check_for_document_related_terms(user_input):
            result = f"The document related to your query is being processed."
        else:
            result = ai_chat(user_input)
        return render_template("index.html", result=result)
    return render_template("index.html", result="")

@app.route("/settings", methods=["GET", "POST"])
def settings():
    global SEARCH_DEPTH, FALLBACK_TO_AI_CHAT, LOOP_UNTIL_SUCCESS, DOCUMENTS_DIR, MIN_SCORE_THRESHOLD, stock_name_to_symbol, document_terms, stock_terms, language_to_country_code, language_to_output_format
    if request.method == "POST":
        try:
            SEARCH_DEPTH = int(request.form.get("SEARCH_DEPTH", SEARCH_DEPTH))
            FALLBACK_TO_AI_CHAT = request.form.get("FALLBACK_TO_AI_CHAT", "on") == "on"
            LOOP_UNTIL_SUCCESS = request.form.get("LOOP_UNTIL_SUCCESS", "on") == "on"
            DOCUMENTS_DIR = request.form.get("DOCUMENTS_DIR", DOCUMENTS_DIR)
            MIN_SCORE_THRESHOLD = int(request.form.get("MIN_SCORE_THRESHOLD", MIN_SCORE_THRESHOLD))
            
            # Update stock_name_to_symbol
            stock_name_to_symbol = dict(item.split(':') for item in request.form.get('stock_name_to_symbol', '').split(';') if ':' in item)
            
            # Update document_terms
            document_terms = dict(item.split(':') for item in request.form.get('document_terms', '').split(';') if ':' in item)
            
            # Update stock_terms
            stock_terms = dict(item.split(':') for item in request.form.get('stock_terms', '').split(';') if ':' in item)
            
            # Update language_to_country_code
            language_to_country_code = dict(item.split(':') for item in request.form.get('language_to_country_code', '').split(';') if ':' in item)
            
            # Update language_to_output_format
            language_to_output_format = dict(item.split(':') for item in request.form.get('language_to_output_format', '').split(';') if ':' in item)

            docs_logger.info("Settings updated.")
        except Exception as e:
            logging.error(f"Error updating settings: {e}")
    return render_template("settings.html")

@app.route("/reset", methods=["POST"])
def reset():
    global SEARCH_DEPTH, FALLBACK_TO_AI_CHAT, LOOP_UNTIL_SUCCESS, DOCUMENTS_DIR, MIN_SCORE_THRESHOLD, stock_name_to_symbol, document_terms, stock_terms, language_to_country_code, language_to_output_format
    SEARCH_DEPTH = 40
    FALLBACK_TO_AI_CHAT = True
    LOOP_UNTIL_SUCCESS = False
    DOCUMENTS_DIR = os.path.expanduser("~/Documents")
    MIN_SCORE_THRESHOLD = 8
    stock_name_to_symbol = {
        "apple": "AAPL",
        "volvo": "VOLV-B.ST",
        "volkswagen": "VOW3.DE",
        "l'oréal": "OR.PA",
        "equinor": "EQNR.OL",
        "asml": "ASML.AS",
    }
    document_terms = {
        "english": "document",
        "swedish": "dokument",
        "german": "dokument",
        "french": "document",
        "spanish": "documento",
        "italian": "documento",
        "norwegian": "dokument",
        "dutch": "document",
    }
    stock_terms = {
        "english": "stock",
        "swedish": "aktie",
        "german": "aktie",
        "french": "action",
        "spanish": "acción",
        "italian": "azione",
        "norwegian": "aksje",
        "dutch": "aandeel",
    }
    language_to_country_code = {
        "swedish": ".ST",
        "english": "",
        "german": ".DE",
        "french": ".PA",
        "spanish": ".MC",
        "italian": ".MI",
        "norwegian": ".OL",
        "dutch": ".AS",
    }
    language_to_output_format = {
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
    docs_logger.info("Settings reset.")
    return redirect(url_for('settings'))

if __name__ == "__main__":
    app.run(debug=True)
