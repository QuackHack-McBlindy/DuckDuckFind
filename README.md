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
- **Multi-Domain Query Handling:** From sports schedules to store hours, DuckDuckFind can handle a wide range of queries, offering deep insights and detailed answers.
- **Higly Configurable:** Customize search depth, logging, document directories, and by controlling the score system - you can fine tune to your specific needs. 

## **Getting Started**

To get started with DuckDuckFind, follow these steps:

### **1. Clone the Repository:**

   Clone the DuckDuckFind repository to your local machine and navigate into it.

  ```
  git clone https://github.com/QuackHack-McBlindy/duckduckfind.git
  cd duckduckfind
  ```

### **2. Build and Run the Project Using Docker:**

   Use Docker to build and run DuckDuckFind.

  ```
  docker compose up -d --build
  # don't like containers? you can run script as is
  # chmod +x ddf.py
  # sudo mv ddf.py /usr/local/bin/ddf
  # § ddf "document how does ducks sound?"
  ```

This will set up and run DuckDuckFind in the background, at http://localhost:5111/ ready to handle your queries.

### **3. Settings:**

   Go see settings.

  ```
  http://localhost:5556/settings
  # default values
  # Search Depth: 40
  # Fallback to AI Chat: 1
  # Loop Until Success: 0
  # Minimal Score Threshold: 8
  ```



## **Example Usage**

   *just start qwackin',*   
   *ducks should handle the rest.*

  ```
  curl -X POST http://localhost:5556/ -H "Content-Type: application/json" -d '{"query": "User Qwack Here"}'
  ```

## **Contributing**

We welcome contributions from the community to help make DuckDuckFind even better!


### **Suggestions and Feedback**

If you have suggestions or encounter any issues, please open an issue on GitHub. Include as much detail as possible, such as the language, region, or specific scenario where you encountered the issue.

### **Contributing Documentation**

If you're interested in improving the project's documentation, we welcome contributions to the README, code comments, or other project docs.


## **Limitations and Disclaimers**

- **Use of yfinance:** DuckDuckFind utilizes the yfinance library to retrieve stock prices. Please ensure you read and agree to the Yahoo Finance Terms of Service before using this feature.

🎈 **Thank You** 🎈


## **Questions?**

