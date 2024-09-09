# /app/services/stocks/price.py
# custom responses for english, swedish, spanish, german, french, italian, portuguese, dutch, polish, russian
import yfinance as yf
import re
import argparse
import ast
import os
import requests_cache
import matplotlib.pyplot as plt
from settings import get_setting, get_dict_setting
from rapidfuzz import process, fuzz
from pytickersymbols import PyTickerSymbols
from itertools import combinations
from duckduckgo_search import DDGS
from datetime import datetime, timedelta
from langdetect import detect, LangDetectException
from langcodes import Language
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter

print("/app/services/stocks/price.py has been imported successfully!")

# Define a class for rate-limiting and caching
class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass

# Create a cached session with rate-limiting
session = CachedLimiterSession(
    limiter=Limiter(RequestRate(2, Duration.SECOND*5)),  # max 2 requests per 5 seconds
    bucket_class=MemoryQueueBucket,
    backend=SQLiteCache("yfinance.cache"),
)
session.headers['User-agent'] = 'my-program/1.0'

default_language = get_setting("DEFAULT_LANGUAGE")
language_to_country_code = get_dict_setting("language_to_country_code")
stock_name_to_symbol = get_dict_setting("stock_name_to_symbol")
language_to_output_format = get_dict_setting("language_to_output_format")

# TODO Output Settings
time_phrases = {
    "english": {
        "last (\d+) months?": lambda x: ("", datetime.now() - timedelta(days=int(x)*30), datetime.now()),
        "last (\d+) weeks?": lambda x: ("", datetime.now() - timedelta(weeks=int(x)), datetime.now()),
        "last (\d+) years?": lambda x: ("", datetime.now() - timedelta(days=int(x)*365), datetime.now()),
        "last year": lambda x: ("1y", None, None),
        "last (\d+) days?": lambda x: ("", datetime.now() - timedelta(days=int(x)), datetime.now()),
        "last month": lambda x: ("1mo", None, None),
        "last 6 months": lambda x: ("6mo", None, None)
    },
    "swedish": {
        "senaste (\d+) månader?": lambda x: ("", datetime.now() - timedelta(days=int(x)*30), datetime.now()),
        "senaste (\d+) veckor?": lambda x: ("", datetime.now() - timedelta(weeks=int(x)), datetime.now()),
        "senaste (\d+) år?": lambda x: ("", datetime.now() - timedelta(days=int(x)*365), datetime.now()),
        "senaste året": lambda x: ("1y", None, None),
        "senaste (\d+) dagar?": lambda x: ("", datetime.now() - timedelta(days=int(x)), datetime.now()),
        "senaste månaden": lambda x: ("1mo", None, None),
        "senaste 6 månader": lambda x: ("6mo", None, None)
    },
    "spanish": {
        "últimos (\d+) meses?": lambda x: ("", datetime.now() - timedelta(days=int(x)*30), datetime.now()),
        "últimas (\d+) semanas?": lambda x: ("", datetime.now() - timedelta(weeks=int(x)), datetime.now()),
        "últimos (\d+) años?": lambda x: ("", datetime.now() - timedelta(days=int(x)*365), datetime.now()),
        "el último año": lambda x: ("1y", None, None),
        "últimos (\d+) días?": lambda x: ("", datetime.now() - timedelta(days=int(x)), datetime.now()),
        "el último mes": lambda x: ("1mo", None, None),
        "últimos 6 meses": lambda x: ("6mo", None, None)
    },
   "german": {
        "letzten (\d+) Monate?": lambda x: ("", datetime.now() - timedelta(days=int(x)*30), datetime.now()),
        "letzten (\d+) Wochen?": lambda x: ("", datetime.now() - timedelta(weeks=int(x)), datetime.now()),
        "letzten (\d+) Jahre?": lambda x: ("", datetime.now() - timedelta(days=int(x)*365), datetime.now()),
        "letztes Jahr": lambda x: ("1y", None, None),
        "letzten (\d+) Tage?": lambda x: ("", datetime.now() - timedelta(days=int(x)), datetime.now()),
        "letzten Monat": lambda x: ("1mo", None, None),
        "letzten 6 Monate": lambda x: ("6mo", None, None)
    },
    "french": {
        "derniers (\d+) mois": lambda x: ("", datetime.now() - timedelta(days=int(x)*30), datetime.now()),
        "dernières (\d+) semaines": lambda x: ("", datetime.now() - timedelta(weeks=int(x)), datetime.now()),
        "dernières (\d+) années": lambda x: ("", datetime.now() - timedelta(days=int(x)*365), datetime.now()),
        "l'année dernière": lambda x: ("1y", None, None),
        "derniers (\d+) jours": lambda x: ("", datetime.now() - timedelta(days=int(x)), datetime.now()),
        "le mois dernier": lambda x: ("1mo", None, None),
        "les 6 derniers mois": lambda x: ("6mo", None, None)
    },
    "italian": {
        "ultimi (\d+) mesi": lambda x: ("", datetime.now() - timedelta(days=int(x)*30), datetime.now()),
        "ultime (\d+) settimane": lambda x: ("", datetime.now() - timedelta(weeks=int(x)), datetime.now()),
        "ultimi (\d+) anni": lambda x: ("", datetime.now() - timedelta(days=int(x)*365), datetime.now()),
        "l'anno scorso": lambda x: ("1y", None, None),
        "ultimi (\d+) giorni": lambda x: ("", datetime.now() - timedelta(days=int(x)), datetime.now()),
        "l'ultimo mese": lambda x: ("1mo", None, None),
        "ultimi 6 mesi": lambda x: ("6mo", None, None)
    },
    "portuguese": {
        "últimos (\d+) meses": lambda x: ("", datetime.now() - timedelta(days=int(x)*30), datetime.now()),
        "últimas (\d+) semanas": lambda x: ("", datetime.now() - timedelta(weeks=int(x)), datetime.now()),
        "últimos (\d+) anos": lambda x: ("", datetime.now() - timedelta(days=int(x)*365), datetime.now()),
        "ano passado": lambda x: ("1y", None, None),
        "últimos (\d+) dias": lambda x: ("", datetime.now() - timedelta(days=int(x)), datetime.now()),
        "último mês": lambda x: ("1mo", None, None),
        "últimos 6 meses": lambda x: ("6mo", None, None)
    },
    "dutch": {
        "laatste (\d+) maanden": lambda x: ("", datetime.now() - timedelta(days=int(x)*30), datetime.now()),
        "laatste (\d+) weken": lambda x: ("", datetime.now() - timedelta(weeks=int(x)), datetime.now()),
        "laatste (\d+) jaren": lambda x: ("", datetime.now() - timedelta(days=int(x)*365), datetime.now()),
        "vorig jaar": lambda x: ("1y", None, None),
        "laatste (\d+) dagen": lambda x: ("", datetime.now() - timedelta(days=int(x)), datetime.now()),
        "vorige maand": lambda x: ("1mo", None, None),
        "laatste 6 maanden": lambda x: ("6mo", None, None)
    },
    "polish": {
        "ostatnie (\d+) miesiące": lambda x: ("", datetime.now() - timedelta(days=int(x)*30), datetime.now()),
        "ostatnie (\d+) tygodnie": lambda x: ("", datetime.now() - timedelta(weeks=int(x)), datetime.now()),
        "ostatnie (\d+) lata": lambda x: ("", datetime.now() - timedelta(days=int(x)*365), datetime.now()),
        "ostatni rok": lambda x: ("1y", None, None),
        "ostatnie (\d+) dni": lambda x: ("", datetime.now() - timedelta(days=int(x)), datetime.now()),
        "ostatni miesiąc": lambda x: ("1mo", None, None),
        "ostatnie 6 miesięcy": lambda x: ("6mo", None, None)
    },
    "russian": {
        "последние (\d+) месяцы": lambda x: ("", datetime.now() - timedelta(days=int(x)*30), datetime.now()),
        "последние (\d+) недели": lambda x: ("", datetime.now() - timedelta(weeks=int(x)), datetime.now()),
        "последние (\d+) года": lambda x: ("", datetime.now() - timedelta(days=int(x)*365), datetime.now()),
        "прошлый год": lambda x: ("1y", None, None),
        "последние (\d+) дни": lambda x: ("", datetime.now() - timedelta(days=int(x)), datetime.now()),
        "прошлый месяц": lambda x: ("1mo", None, None),
        "последние 6 месяцев": lambda x: ("6mo", None, None)
    }
}

def generate_stock_graph(history_data, symbol, save_path="/app/app/Media/Photos"):
    """
    Generate and save a stock price graph based on the historical data.
    :param history_data: Pandas DataFrame containing historical stock price data.
    :param symbol: The stock symbol for labeling the graph.
    :param save_path: The directory where the graph will be saved. Defaults to '/app/Media/Photos'.
    """
    if history_data.empty:
        print(f"No historical data available for {symbol}")
        return
    os.makedirs(save_path, exist_ok=True)
    
    # Define the file name
    filename = f"{symbol}_stock_price.png"
    full_path = os.path.join(save_path, filename)
    
    plt.figure(figsize=(10, 6))
    plt.plot(history_data.index, history_data['Close'], label=f"{symbol} Close Price")
    plt.title(f"{symbol} Stock Price Over Time") # TODO Insert proper history label
    plt.xlabel("Date")
    plt.ylabel("Price (in USD)") # TODO Extend currencies
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45)  # Rotate the x-axis labels for better readability

    plt.tight_layout() # TODO Layout setting
    plt.savefig(filename, format='png')
    print(f"Stock price graph saved to {filename}")    
    plt.clf() # Clear the plot to free memory for subsequent plots
    return filename  

def detect_language(text):
    """Detect the language of the query."""
    try:
        language_code = detect(text)
        language_name = Language.get(language_code).language_name().lower()
        return language_name
    except LangDetectException:
        default_language = get_setting("DEFAULT_LANGUAGE")
        return default_language or "english" 

def parse_time_period(query, detected_language):
    """
    Parse the time period from the query string based on the detected language.
    :param query: Natural language query (e.g., "last 3 months", "last year")
    :param detected_language: Detected language from the query
    :return: A tuple (period, start, end) where one of them is set and others are None
    """
    now = datetime.now()
    
    language_phrases = time_phrases.get(detected_language, time_phrases.get(default_language, time_phrases["english"]))
    
    # Loop through the time patterns for the detected language
    for pattern, handler in language_phrases.items():
        match = re.search(pattern, query)
        if match:
            return handler(match.group(1) if match.groups() else None)
    
    # Default to 1 month if no pattern is matched
    return ("1mo", None, None)


def fetch_stock_data(symbol, period="1mo", start=None, end=None):
    """Fetch stock data using yfinance with optional period or date range."""
    symbol = symbol.replace(" ", "-")
    stock = yf.Ticker(symbol, session=session)
    
    # Fetch data either based on period or start/end date range
    if start and end:
        history_data = stock.history(start=start, end=end)
    else:
        history_data = stock.history(period=period)
    

    if not history_data.empty:
        price = history_data['Close'].iloc[-1]
        initial_price = history_data['Close'].iloc[0]
        percentage_change = ((price - initial_price) / initial_price) * 100
        
        return {
            "symbol": symbol,
            "price": price,
            "initial_price": initial_price,
            "percentage_change": percentage_change,
            "history": history_data
        }
    
    return {"error": f"No price data found for {symbol}. This stock may be delisted or not available."}


def format_output(symbol, price, percentage_change, period, language):
    """Format the stock price output based on language, including price change."""
    
    # Handle direction of the change based on language
    if language == "english":
        change_direction = "increased" if percentage_change >= 0 else "decreased"
    elif language == "swedish":
        change_direction = "gått upp" if percentage_change >= 0 else "gått ner"
    elif language == "french":
        change_direction = "augmenté" if percentage_change >= 0 else "diminué"
    elif language == "german":
        change_direction = "gestiegen" if percentage_change >= 0 else "gefallen"
    elif language == "spanish":
        change_direction = "aumentado" if percentage_change >= 0 else "disminuido"
    elif language == "italian":
        change_direction = "aumentato" if percentage_change >= 0 else "diminuito"
    elif language == "portuguese":
        change_direction = "aumentado" if percentage_change >= 0 else "diminuído"
    elif language == "dutch":
        change_direction = "gestegen" if percentage_change >= 0 else "gedaald"
    elif language == "polish":
        change_direction = "wzrosła" if percentage_change >= 0 else "spadła"
    elif language == "russian":
        change_direction = "увеличился" if percentage_change >= 0 else "уменьшился"
    else:
        change_direction = "increased" if percentage_change >= 0 else "decreased"

    # Period replacements based on language
    period_replacements = {
        "english": {"1y": "year", "1mo": "month", "1w": "week", "1d": "day"},
        "swedish": {"1y": "året", "1mo": "månaden", "1w": "veckan", "1d": "dagen"},
        "french": {"1y": "an", "1mo": "mois", "1w": "semaine", "1d": "jour"},
        "german": {"1y": "Jahr", "1mo": "Monat", "1w": "Woche", "1d": "Tag"},
        "italian": {"1y": "anno", "1mo": "mese", "1w": "settimana", "1d": "giorno"},
        "portuguese": {"1y": "ano", "1mo": "mês", "1w": "semana", "1d": "dia"},
        "dutch": {"1y": "jaar", "1mo": "maand", "1w": "week", "1d": "dag"},
        "polish": {"1y": "rok", "1mo": "miesiąc", "1w": "tydzień", "1d": "dzień"},
        "russian": {"1y": "год", "1mo": "месяц", "1w": "неделя", "1d": "день"},     
    }
    
    # Replace shorthand period with full-text equivalent based on the detected language
    if language in period_replacements:
        for shorthand, full_text in period_replacements[language].items():
            period = period.replace(shorthand, full_text)
    
    # Handle Swedish-specific currency format
    if language == "swedish":
        if symbol.endswith(".ST"):
            output_format = language_to_output_format["swedish_kr"]  # Use kr for Swedish stocks
        else:
            output_format = language_to_output_format["swedish_dollar"]  # Use dollar for others
    else:
        # Retrieve the correct language format or default to English
        output_format = language_to_output_format.get(language, language_to_output_format["english"])

    # Format and return the output message
    return output_format.format(symbol=symbol, price=price, percentage_change=abs(percentage_change), period=period, change_direction=change_direction)


def list_all_stocks():
    """List all stocks using PyTickerSymbols."""
    stock_data = PyTickerSymbols()
    indices = stock_data.get_all_indices()
    all_stocks = []
    for index in indices:
        stocks = stock_data.get_stocks_by_index(index)
        for stock in stocks:
            all_stocks.append(stock['name'])
    return all_stocks

def find_closest_match(query, stock_names):
    """Find the closest match for the query using fuzzy matching."""
    words = query.split()
    best_matches = []
    for r in range(len(words), 0, -1):
        for combo in combinations(words, r):
            combo_query = ' '.join(combo)
            matches = process.extract(combo_query, stock_names, scorer=fuzz.partial_ratio, limit=5)
            for match in matches:
                best_matches.append((match[0], match[1], len(combo_query)))
    if best_matches:
        best_matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        top_match, score, _ = best_matches[0]
        return top_match, score
    else:
        return None, None

def find_stock_symbol_by_name(stock_name):
    """Find stock symbol by name using PyTickerSymbols."""
    stock_data = PyTickerSymbols()
    indices = [
        'AEX', 'BEL 20', 'CAC 40', 'DAX', 'DOW JONES', 'FTSE 100',
        'IBEX 35', 'MDAX', 'NASDAQ 100', 'OMX Helsinki 15',
        'OMX Helsinki 25', 'OMX Stockholm 30', 'S&P 100', 'S&P 500',
        'SDAX', 'SMI', 'TECDAX', 'MOEX'
    ]
    for index in indices:
        try:
            stocks = stock_data.get_stocks_by_index(index)
            for stock in stocks:
                if stock_name.lower() in stock['name'].lower():
                    return stock['symbol']
        except Exception as e:
            print(f"An error occurred while processing index {index}: {e}")
    return None


def get_stock_price(query):
    """Main function to get the stock price based on a query."""
    detected_language = detect_language(query)
    country_code = language_to_country_code.get(detected_language, "")
    
    # Parse time period based on the detected language
    period, start, end = parse_time_period(query, detected_language)
    print(f"Detected period: {period}")

    if period is None:
        period = "1mo"  # Default to 1 month if no period is specified
    
    for name, symbol in stock_name_to_symbol.items():
        if name.lower() in query.lower():
            try:
                result = fetch_stock_data(symbol, period=period, start=start, end=end)
                if "error" not in result:
                    result['period'] = period
                    print(f"Detected period: {period}")
                    
                    graph_path = generate_stock_graph(result['history'], symbol)
                    result['graph_path'] = graph_path  
                    return result
            except Exception as e:
                return {"error": str(e), "period": period}  # Return period with the error
    
    # Fallback to searching for the stock symbol and generating a graph
    all_stock_names = list_all_stocks()
    closest_match, score = find_closest_match(query, all_stock_names)
    if closest_match and score >= 80:
        symbol = find_stock_symbol_by_name(closest_match)
        if symbol:
            if country_code and not symbol.endswith(country_code):
                symbol += country_code
            result = fetch_stock_data(symbol, period=period, start=start, end=end)
            if "error" not in result:
                result['period'] = period  # Ensure period is included in the result
                print(f"Detected period: {period}")
                graph_path = generate_stock_graph(result['history'], symbol)
                result['graph_path'] = graph_path  
            return result
    
    # Handle DuckDuckGo symbol search fallback
    ddg = DDGS()
    try:
        results = ddg.chat(query + " stock symbol")
        match = re.search(r'\b[A-Z0-9]{2,5}(?:-[A-Z])?\b', results.get('text', ''))
        if match:
            symbol = match.group(0)
            if country_code and not symbol.endswith(country_code):
                symbol += country_code
            result = fetch_stock_data(symbol, period=period, start=start, end=end)
            if "error" not in result:
                result['period'] = period  # Ensure period is included in the result
                graph_path = generate_stock_graph(result['history'], symbol)
                result['graph_path'] = graph_path  
            return result
    except Exception as e:
        return {"error": f"Error fetching stock symbol from DuckDuckGo: {str(e)}", "period": period}
    
    return {"error": "Sorry, stock symbol not recognized", "period": period}




def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Get the stock price based on the query.")
    parser.add_argument('query', type=str, help="The query containing the stock name.")
    args = parser.parse_args()
    
    query = args.query
    result = get_stock_price(query)
    if "error" in result:
        print(result["error"])
    else:
        symbol = result["symbol"]
        price = result["price"]
        detected_language = detect_language(query)
        formatted_output = format_output(symbol, price, detected_language)
        print(formatted_output)

