# /app/services/stocks/price.py
import re
import argparse
import ast
from settings import get_setting, get_dict_setting
from rapidfuzz import process, fuzz
from pytickersymbols import PyTickerSymbols
from itertools import combinations
from duckduckgo_search import DDGS
import yfinance as yf
from langdetect import detect, LangDetectException
from langcodes import Language
import requests_cache
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


language_to_country_code = get_dict_setting("language_to_country_code")
stock_name_to_symbol = get_dict_setting("stock_name_to_symbol")
language_to_output_format = get_dict_setting("language_to_output_format")


def detect_language(text):
    """Detect the language of the query."""
    try:
        language_code = detect(text)
        language_name = Language.get(language_code).language_name().lower()
        return language_name
    except LangDetectException:
        default_language = get_setting("DEFAULT_LANGUAGE")
        return default_language or "english" 

def fetch_stock_data(symbol):
    """Fetch stock data using yfinance."""
    symbol = symbol.replace(" ", "-")
    stock = yf.Ticker(symbol, session=session)
    history_data = stock.history(period='1mo')
    if not history_data.empty:
        price = history_data['Close'].iloc[-1]
        return {"symbol": symbol, "price": price}
    return {"error": f"No price data found for {symbol}. This stock may be delisted or not available."}

def format_output(symbol, price, language):
    """Format the stock price output based on language."""
    if language == "swedish":
        if symbol.endswith(".ST"):
            output_format = language_to_output_format["swedish_kr"]
        else:
            output_format = language_to_output_format["swedish_dollar"]
    else:
        output_format = language_to_output_format.get(language, language_to_output_format["english"])
    return output_format.format(symbol=symbol, price=price)

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

    # Check predefined symbols first
    for name, symbol in stock_name_to_symbol.items():
        if name.lower() in query.lower():
            try:
                return fetch_stock_data(symbol)
            except Exception as e:
                return {"error": str(e)}
    
    all_stock_names = list_all_stocks()
    closest_match, score = find_closest_match(query, all_stock_names)
    if closest_match and score >= 80:
        symbol = find_stock_symbol_by_name(closest_match)
        if symbol:
            if country_code and not symbol.endswith(country_code):
                symbol += country_code
            return fetch_stock_data(symbol)
    
    ddg = DDGS()
    try:
        results = ddg.chat(query + " stock symbol")
        match = re.search(r'\b[A-Z0-9]{2,5}(?:-[A-Z])?\b', results.get('text', ''))
        if match:
            symbol = match.group(0)
            if country_code and not symbol.endswith(country_code):
                symbol += country_code
            return fetch_stock_data(symbol)
    except Exception as e:
        print(f"Error fetching stock symbol from DuckDuckGo: {e}")
    
    return {"error": "Sorry, stock symbol not recognized"}

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

