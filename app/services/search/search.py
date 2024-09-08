# /app/services/search/search.py

print("/app/services/search/search.py has been imported successfully!")

import requests
from bs4 import BeautifulSoup
from settings import get_setting
from duckduckgo_search import DDGS
import logging
import subprocess

REGION = get_setting("REGION")
MIN_SCORE_THRESHOLD = get_setting("MIN_SCORE_THRESHOLD")
IMPORTANT_PHRASES = get_setting("important_phrases")
SEARCH_DEPTH = get_setting("SEARCH_DEPTH")
FALLBACK_TO_AI_CHAT = get_setting("FALLBACK_TO_AI_CHAT")
LOOP_UNTIL_SUCCESS = get_setting("LOOP_UNTIL_SUCCESS")

ddgs = DDGS()


def improved_string_matching(description, user_input):
    description = description.lower()
    user_input_words = user_input.lower().split()
    
    score = sum(2 if word in IMPORTANT_PHRASES else 1 for word in user_input_words if word in description)
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
        
        for attempt in range(3):  # Try up to 3 times with different headers
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
                
                break  # If no errors, break out of retry loop

            except requests.RequestException:
                continue
        
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
    return None

def fallback_to_ai_chat(user_input, data_block=None):
    try:
        ddg = DDGS()
        if data_block:
            combined_input = f"{user_input}\n\nData Block:\n{data_block}"
        else:
            combined_input = user_input
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


def search_web_for_answer(query):
    ddgs = DDGS()
    results = ddgs.text(query)

    if not results:
        return "No search results were found."

    attempt_count = 0

    while attempt_count < SEARCH_DEPTH or LOOP_UNTIL_SUCCESS:
        description_answer = parse_description_for_answer(results, query)
        if description_answer:
            return description_answer

        for index, result in enumerate(results[:SEARCH_DEPTH]):
            url = result['href']
            page_source_answer = inspect_page_source(url, query)
            if page_source_answer:
                
                return fallback_to_ai_chat(query, page_source_answer)

        attempt_count += 1
        if not LOOP_UNTIL_SUCCESS:
            break

    if FALLBACK_TO_AI_CHAT:
        return fallback_to_ai_chat(query)
    else:
        return "I searched the web but couldn't find a clear answer to your question." 
