
import argparse
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import re
from flask import Flask, request, jsonify, Response
from duckduckgo_search import DDGS
from transformers import pipeline
import json
import yfinance as yf
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### --> Global Variables <-- ###
doc_dir = 'documents'


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

# Load the index
def load_index(filename='index.pkl'):
    with open(filename, 'rb') as f:
        return pickle.load(f)

# Load the documents
def load_documents(doc_dir):
    documents = {}
    for filename in os.listdir(doc_dir):
        if filename.endswith(".txt"):  # assuming documents are in .txt format
            with open(os.path.join(doc_dir, filename), 'r', encoding='utf-8') as f:
                documents[filename] = f.read()
    return documents

# Find the most relevant section within the document
def find_relevant_section(document, query, model):
    # Split document into sections based on the pattern ####
    sections = re.split(r'\n#+\n', document)
    
    # Encode sections and query
    section_embeddings = model.encode(sections, convert_to_tensor=True)
    query_embedding = model.encode([query], convert_to_tensor=True)
    
    # Compute cosine similarity between query and each section
    similarities = cosine_similarity(query_embedding, section_embeddings)[0]
    
    # Find the section with the highest similarity
    most_similar_idx = np.argmax(similarities)
    
    # Return the most relevant section
    return sections[most_similar_idx].strip()

# Search function
def search(query, model, embeddings, documents):
    query_embedding = model.encode([query], convert_to_tensor=True)
    similarities = cosine_similarity(query_embedding, embeddings)[0]
    most_similar_idx = np.argmax(similarities)
    most_similar_doc = list(documents.keys())[most_similar_idx]
    
    # Get the most similar document's content
    document = documents[most_similar_doc]
    
    # Find and return the most relevant section within the document
    relevant_section = find_relevant_section(document, query, model)
    return relevant_section

# Index documents
def index_documents(documents):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    doc_texts = list(documents.values())
    embeddings = model.encode(doc_texts, convert_to_tensor=True)
    return model, embeddings

# Save the index
def save_index(model, embeddings, filename='index.pkl'):
    with open(filename, 'wb') as f:
        pickle.dump((model, embeddings), f)

app = Flask(__name__)

# Initialize DDGS globally
ddg = DDGS()

# Initialize transformers pipeline for sentiment analysis (or replace with appropriate task)
model = pipeline('sentiment-analysis', model='./model')

# Static dictionary for stock names to symbols (expand as needed)
stock_name_to_symbol = {
    "nvidia": "NVDA",
    "apple": "AAPL",
    "google": "GOOGL",
    "microsoft": "MSFT",
    # Add more stock names and symbols as needed
}

def create_response(result):
    response_json = json.dumps(result, ensure_ascii=False)
    return Response(response_json, content_type='application/json; charset=utf-8')

def extract_opening_hours(text):
    # Extended regex pattern to capture various opening hour formats
    pattern = r"""
        (?i)                           # Case-insensitive matching
        (?:
            (?:m[åa]n(?:dag)?|tis(?:dag)?|ons(?:dag)?|tors(?:dag)?|fre(?:dag)?|l[öo]r(?:dag)?|s[öo]n(?:dag)?|
            mon(?:day)?|tue(?:sday)?|wed(?:nesday)?|thu(?:rsday)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?|
            today|idag)\s*[:.,]?\s*     # Match day names in Swedish or English, with optional separators
        )?
        (\d{1,2}[:.]\d{2})\s*(?:AM|PM|am|pm)?\s*(-|to)\s*(\d{1,2}[:.]\d{2})\s*(?:AM|PM|am|pm)?  # Match time ranges like 07:30-23:00 or 8:00 AM - 10:00 PM
        |
        (?:m[åa]n(?:dag)?|tis(?:dag)?|ons(?:dag)?|tors(?:dag)?|fre(?:dag)?|l[öo]r(?:dag)?|s[öo]n(?:dag)?|
        mon(?:day)?|tue(?:sday)?|wed(?:nesday)?|thu(?:rsday)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?)
        [-]\s*(\d{1,2})[:.](\d{2})\s*(-|to)\s*(\d{1,2})[:.](\d{2})\s*(?:AM|PM|am|pm)?  # Match days combined with a single time range like mån-lör 8-22
    """
    matches = re.findall(pattern, text, re.VERBOSE)
    
    # Flatten the list of tuples and filter out empty strings
    flattened_matches = ["".join(match).strip() for match in matches if any(match)]
    
    if flattened_matches:
        return " ; ".join(flattened_matches).strip()
    
    return None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

@app.route('/search/opening-hours', methods=['POST'])
def search_opening_hours():
    data = request.get_json()
    query = data.get('query') if data else None
    
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    results = ddg.text(query, max_results=50)
    
    if not results:
        return jsonify({"error": "No results found"}), 404
    
    for result in results:
        # Filter out results that do not contain any numbers
        if not re.search(r'\d', result['body']):
            continue
        
        # Try to extract opening hours using the improved regex
        opening_hours = extract_opening_hours(result['body'])
        if opening_hours:
            response = {
                "title": result['title'],
                "href": result['href'],
                "opening_hours": opening_hours
            }
            return create_response(response)
    
    return jsonify({"error": "No relevant information found"}), 404

def extract_opening_hours(text):
    # Improved regex pattern to capture a variety of opening hour formats
    pattern = r'(Öppettider|Opening hours|Öppettider:)\s*([^\n]*)|(\d{1,2}[:.]?\d{0,2}\s*(AM|PM)?\s*(-|to)\s*\d{1,2}[:.]?\d{0,2}\s*(AM|PM)?)|Open 24 hours|Closed'
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    # Join all matches to form a complete string of opening hours
    if matches:
        return " ".join(["".join(match) for match in matches]).strip()
    
    return None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

@app.route('/search/text', methods=['POST'])
def search_text():
    data = request.get_json()
    query = data.get('query') if data else None
    
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    # Perform text search using DuckDuckGo
    results = ddg.text(query, max_results=50)
    
    if not results:
        return jsonify({"error": "No results found"}), 404
    
    # Analyze results using transformers model
    analyses = model([result['body'] for result in results])
    best_result = max(zip(results, analyses), key=lambda x: x[1]['score'])[0]
    
    return create_response(best_result)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

@app.route('/search/images', methods=['POST'])
def search_images():
    data = request.get_json()
    query = data.get('query') if data else None
    
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    results = ddg.images(query, max_results=50)
    
    if not results:
        return jsonify({"error": "No results found"}), 404
    
    return create_response(results)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

@app.route('/search/videos', methods=['POST'])
def search_videos():
    data = request.get_json()
    query = data.get('query') if data else None
    
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    results = ddg.videos(query, max_results=50)
    
    if not results:
        return jsonify({"error": "No results found"}), 404
    
    return create_response(results)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

@app.route('/search/news', methods=['POST'])
def search_news():
    data = request.get_json()
    query = data.get('query') if data else None
    
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    results = ddg.news(query, max_results=50)
    
    if not results:
        return jsonify({"error": "No results found"}), 404
    
    return create_response(results)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

@app.route('/search/maps', methods=['POST'])
def search_maps():
    data = request.get_json()
    query = data.get('query') if data else None
    
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    results = ddg.maps(query, max_results=50)
    
    if not results:
        return jsonify({"error": "No results found"}), 404
    
    return create_response(results)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

@app.route('/search/translate', methods=['POST'])
def search_translate():
    data = request.get_json()
    query = data.get('query') if data else None
    to_lang = data.get('to') if data else "en"
    
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    results = ddg.translate(query, to=to_lang)
    
    if not results:
        return jsonify({"error": "No results found"}), 404
    
    return create_response(results)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

@app.route('/search/suggestions', methods=['POST'])
def search_suggestions():
    data = request.get_json()
    query = data.get('query') if data else None
    
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    results = ddg.suggestions(query)
    
    if not results:
        return jsonify({"error": "No results found"}), 404
    
    return create_response(results)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

@app.route('/search/answers', methods=['POST'])
def search_answers():
    data = request.get_json()
    query = data.get('query') if data else None
    
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    results = ddg.answers(query)
    
    if not results:
        return jsonify({"error": "No results found"}), 404
    
    return create_response(results)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

@app.route('/search/chat', methods=['POST'])
def search_chat():
    data = request.get_json()
    query = data.get('query') if data else None
    
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    results = ddg.chat(query)
    
    if not results:
        return jsonify({"error": "No results found"}), 404
    
    return create_response(results)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

@app.route('/search/documents', methods=['POST'])
def search_documents():
    data = request.get_json()
    query = data.get('query') if data else None
    
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    # Load the model and embeddings
    model, embeddings = load_index()
    
    # Load the documents
    documents = load_documents(doc_dir)
    
    # Perform search
    result = search(query, model, embeddings, documents)
    
    return create_response({"result": result})

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

@app.route('/update/documents', methods=['POST'])
def update_documents():
    # Load the documents
    documents = load_documents(doc_dir)
    
    # Index the documents
    model, embeddings = index_documents(documents)
    
    # Save the index
    save_index(model, embeddings)
    
    return jsonify({"message": "🦆📄Indexing complete and saved.🎈🎈"})

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

@app.route('/search/stock-price', methods=['POST'])
def stock_price():
    data = request.get_json()
    query = data.get('query') if data else None
    
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Try to find the stock symbol from the predefined list
    for name, symbol in stock_name_to_symbol.items():
        if name.lower() in query.lower():
            try:
                stock = yf.Ticker(symbol)
                price = stock.history(period='1d')['Close'].iloc[-1]
                return jsonify({"symbol": symbol, "price": price})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

    # If stock name is not found in the predefined list, perform a text search to find the symbol
    results = ddg.text(query + " stock symbol", max_results=50)
    
    if not results:
        return jsonify({"error": "No results found"}), 404

    for result in results:
        # Simple regex to extract stock symbol (you can enhance this as needed)
        match = re.search(r'\b[A-Z]{1,5}\b', result['body'])
        if match:
            symbol = match.group(0)
            try:
                stock = yf.Ticker(symbol)
                price = stock.history(period='1d')['Close'].iloc[-1]
                return jsonify({"symbol": symbol, "price": price})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Stock symbol not recognized"}), 404

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5556)
