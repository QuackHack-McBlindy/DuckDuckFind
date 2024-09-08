# ❤️🦆🔍 DuckDuckFind

![DuckDuckFind Logo](https://raw.githubusercontent.com/QuackHack-McBlindy/DuckDuckFind/main/duckduckfind.png)



Welcome to **DuckDuckFind**— a cutting-edge tool that revolutionizes how you search for information across the web and your local files. DuckDuckFind harnesses the power of the DuckDuckGo search engine, intelligent language detection, and advanced web scraping techniques to extract and verify data. Qwack?! —DuckDuckFind also leverages AI to process and refine the information it gathers, ensuring you receive accurate and relevant results every time.

Originally designed for use with voice assistants, DuckDuckFind can be utilized in various other ways. It’s built to handle a wide range of queries, from retrieving stock prices and searching through local documents to pulling relevant information from web pages. Whether you’re checking the next game of your favorite sports team or looking up the opening hours of a local store, DuckDuckFind works to gather and refine this information, providing you with clear and concise answers. It’s a versatile tool that brings advanced search capabilities to your fingertips.


## **Table of Contents**

- [Features](#features)
- [Getting Started](#getting-started)
- [Example Usage](#example-usage)
- [Example Responses](#example-responses)
- [Contributing](#contributing)
- [Limitations and Disclaimers](#limitations-and-disclaimers)
- [Questions?](#questions)

## **Features**

- **Document Search:** Find specific content in your local files with language-specific relevance and context-aware scoring.
- **Stock Price Retrieval:** Instantly retrieve todays stock prices across multiple regions, tailored to your language and location.
- **Smart Web Search with AI:** DuckDuckFind uses DuckDuckGo for web searches, scrapes relevant page content, and employs AI to validate and refine the results.
- **Language Detection and Contextual Understanding:** Automatically detects the language of your queries, providing accurate and culturally relevant responses.
- **Multi-Domain Query Handling:** From sports schedules to store hours and all kinds of departure times, DuckDuckFind can handle a wide range of queries, offering deep insights and detailed answers.
- **Higly Configurable:** Customize all kinds of options from the web UI, logging, document directories, and by controlling the score system - you can fine tune to your specific needs. 
- **Custom Scraping:** Perform configurable web scraping from within the web UI,features include file format output, scheduling annd creation of an EPG service and full management of it. 
- **Display:** A endpont designed specifically for displaying results when searcing for personal images or 
if you prefer, you can output graphs from stock queries.  
- **Link & Conenct Services:** Connect other services. Define and configure trigger words for services, and safely store their API tokens from within the web UI - following security best practice.   

## **Getting Started**

To get started with DuckDuckFind, follow these steps:

### **1. Clone the Repository:**

   Clone the DuckDuckFind repository to your local machine and navigate into it.

  ```
  git clone https://github.com/QuackHack-McBlindy/duckduckfind.git
  cd DuckDuckFind
  ```

### **2. Build and Run the Project Using Docker:**

   Use Docker to build and run DuckDuckFind.

  ```
  docker compose up -d --build
  ```

This will set up and run DuckDuckFind in the background.<br>
http://localhost:5111/ ready to handle your queries.

### **3. Settings:**

   http://localhost:5556/settings <br>
   Go see settings. <br>
   To achieve the best results, you should try to control the scoring system by adjusting the settings.  <br>
   Specifically:

    1. Add words to the Important Phrases list.
    2. Adjust the Minimal Score Threshold.

For each word in your query that matches a word in the search result, the result earns +1 score. If the word also appears in the Important Phrases, it earns an additional +1 score.

Understanding and controlling the score system as much as possible can sometimes be crucial, and the difference between the best result and a *zero* result.<br>


## **Example Usage**

   *just start qwackin',*   
   *ducks should handle the rest.*

  ```
  curl -X POST http://localhost:5556/ -H "Content-Type: application/json" -d '{"query": "User Qwack Here"}'
  ```

If you prefer browser for testing you can converse at  
http://localhost:5556/chat

## **The Viewer**

You can visit the Viewer at http://localhost:5556/viewer  
You can query photos simply by asking to display photos from specific year and they will be displayed in the /viewer.  
As default, the viewer displays photos taken last year (365 days ago) as a slideshow.  


Example query:  
__"How has the Nvidia stock performed the last 6 months?"__  
Response:
_The current stock price of NVDA is: $102.83_

This query will create a graph of the last 6 months closing price  
for the Nvidia stock, and display it in the /Viewer.

![Example Graph](https://raw.githubusercontent.com/QuackHack-McBlindy/DuckDuckFind/main/stock_example.png)



## **Questions?**

