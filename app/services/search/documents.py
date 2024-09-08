# /app/services/search/documents.py

print("/app/services/search/documents.py has been imported successfully!")
import os
import fitz
from settings import get_setting
import pandas as pd
from markdown2 import markdown
from rapidfuzz import fuzz, process


def read_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def read_pdf(file_path):
    text = ""
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()
    return text

def read_csv(file_path):
    df = pd.read_csv(file_path)
    return df.to_string()

def read_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        html = markdown(file.read())
        return html

def search_documents(query, directory='/app/app/Media/Documents'):
    DOCS_CONTEXT_LINES = get_setting("DOCS_CONTEXT_LINES")

    search_term = query.strip()
    if not search_term:
        raise ValueError("The search term cannot be empty.")
    
    results = []
    
    for root, dirs, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            
            if file_path.endswith('.txt'):
                content = read_text_file(file_path)
            elif file_path.endswith('.pdf'):
                content = read_pdf(file_path)
            elif file_path.endswith('.csv'):
                content = read_csv(file_path)
            elif file_path.endswith('.md'):
                content = read_markdown(file_path)
            else:
                continue
            
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if search_term.lower() in line.lower():
                    start = max(0, i - DOCS_CONTEXT_LINES)
                    end = min(len(lines), i + DOCS_CONTEXT_LINES + 1)
                    context = "\n".join(lines[start:end]).strip()
                    results.append(context)
    
    return "\n\n---\n\n".join(results)


