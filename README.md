# **❤️🦆🔍 -> DuckDuckFind**

Welcome to **DuckDuckFind**, an API primarily designed to streamline search operations for voice assistants.

**DuckDuckFind** is a versatile and powerful search API that integrates DuckDuckGo's search capabilities with sentiment analysis, document indexing, and stock price retrieval into a single Flask application. Whether you're searching the web, analyzing sentiment, managing documents, or retrieving stock prices, DuckDuckFind is equipped to handle your needs.

## **Table of Contents**

- [Features](#features)
- [Getting Started](#getting-started)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [Questions?](#questions)


## **Features**

- Search Documents: Index and search your own documents.
- Stock Price Retrieval: Get the latest stock prices.
- Opening Hours: Retrieve business opening hours.
- AI Chat: Engage in conversations with AI.
- Text Search: Search the web for text-based content.
- Image Search: Find images on the web.
- Video Search: Locate videos online.
- News Search: Get the latest news articles.
- Map Search: Search for location-based results.
- Translation: Translate text to different languages.
- Search Suggestions: Get suggestions based on your query.
- Direct Answers: Retrieve direct answers to your questions.


## **Getting Started**

1. **Clone the repository:**

    ```bash
    git clone https://github.com/QuackHack-McBlindy/DuckDuckFind.git
    cd DuckDuckFind
    ```

2. **Run the Setup**: Build and start the Docker container.

    ```bash
    docker compose up -d --build
    ```

3. **Document Structure:** Place your documents in the documents directory. Structure your files as follows:

    ```
    ## DEFINE SEARCH KEYWORDS HERE ##
    Insert your data here.
    ###############################
    ## DEFINE SEARCH KEYWORDS HERE ##
    Insert your data here.
    #########################
    ```

    _Note: The number of hashtags that define each section is not crucial, but at least 4 hashtags should be used._

4. **Update Index:** After modifying the documents directory, re-index your documents.

    ```bash
    curl -X POST http://localhost:5556/update/documents
    ```

## **API Endpoints**

Here are some examples of how to use the API endpoints:

1. **Search Documents**

    Search your indexed documents for relevant content.

    ```bash
    curl -X POST http://localhost:5556/search/documents -H "Content-Type: application/json" -d '{"query": "what does the duck say"}'
    ```

2. **Search Stock Price**

    Retrieve the latest stock price for a given company. Update the predefined stock names in the stock_name_to_symbol dictionary within app.py.

    _Note: The endpoint first checks if the query matches any stock names in the predefined list and, if found, fetches the latest closing price using yfinance. If no match is found, it performs a DuckDuckGo text search to find a relevant stock symbol, extracts it using a regex pattern, and then retrieves and returns the stock price using yfinance._

    ```bash
    curl -X POST http://localhost:5556/search/stock-price -H "Content-Type: application/json" -d '{"query": "What is the stock price of Apple"}'
    ```

3. **Search Opening Hours**

    Retrieve opening hours for businesses. The text is examined using a regular expression pattern to extract various formats of opening hours.

    ```bash
    curl -X POST http://localhost:5556/search/opening-hours -H "Content-Type: application/json" -d '{"query": "Opening hours of Starbucks"}'
    ```

4. **AI Chat**

    Engage in a conversational chat with an AI.

    ```bash
    curl -X POST http://localhost:5556/search/chat -H "Content-Type: application/json" -d '{"query": "Tell me a joke"}'
    ```

5. **Translate**

    Translate text to a specified language.

    ```bash
    curl -X POST http://localhost:5556/search/translate -H "Content-Type: application/json" -d '{"query": "Hello, how are you?", "to": "es"}'
    ```

6. **Search Text**

    Search the web for text-based content. Each result is analyzed using a sentiment analysis model, and the result with the highest sentiment score is selected.

    ```bash
    curl -X POST http://localhost:5556/search/text -H "Content-Type: application/json" -d '{"query": "example search query"}'
    ```

7. **Search Images**

    Search the web for images.

    ```bash
    curl -X POST http://localhost:5556/search/images -H "Content-Type: application/json" -d '{"query": "cats"}'
    ```

8. **Search Videos**

    Search the web for videos.

    ```bash
    curl -X POST http://localhost:5556/search/videos -H "Content-Type: application/json" -d '{"query": "funny dog videos"}'
    ```

9. **Search News**

    Search the web for news articles.

    ```bash
    curl -X POST http://localhost:5556/search/news -H "Content-Type: application/json" -d '{"query": "latest tech news"}'
    ```

10. **Search Maps**

    Search for location-based results.

    ```bash
    curl -X POST http://localhost:5556/search/maps -H "Content-Type: application/json" -d '{"query": "best pizza near me"}'
    ```

11. **Search Suggestions**

    Get search suggestions based on a query.

    ```bash
    curl -X POST http://localhost:5556/search/suggestions -H "Content-Type: application/json" -d '{"query": "python programming"}'
    ```

12. **Search Answers**

    Get direct answers to queries.

    ```bash
    curl -X POST http://localhost:5556/search/answers -H "Content-Type: application/json" -d '{"query": "What is the capital of France?"}'
    ```

13. **Update Documents**

    Re-index your documents when they change or new ones are added.

    ```bash
    curl -X POST http://localhost:5556/update/documents
    ```

14. **Download Model**

    Download and save a pre-trained sentiment analysis model.

    ```bash
    curl -X POST http://localhost:5556/download/model
    ```

## **Contributing**

We welcome contributions from the community to help make DuckDuckFind even better! Below are the guidelines for contributing to the project:

### **Testing**

DuckDuckFind supports searches and functionalities that are influenced by language, location, and other regional settings. To ensure the application works well across different regions and languages, we encourage contributors to test the code in their own local environments. Here are some specific areas to focus on:

1. **Language-Specific Testing**:
   - Test the API endpoints with queries in your native language or other languages you are fluent in.
   - Ensure that the translation feature (`/search/translate`) accurately converts text between your language and others.
   - Verify that sentiment analysis and other text-based features work as expected with non-English queries.

2. **Region-Specific Testing (DuckDuckGo Region Codes)**:
   - DuckDuckGo results can vary based on region codes (e.g., `us-en` for United States, `uk-en` for United Kingdom, etc.). Test the search endpoints with your DuckDuckGo region code to see if the results are relevant and accurate for your location.
   - You can specify the region code when making requests to DuckDuckGo by modifying the query string in the API calls.

3. **Local Business Opening Hours**:
   - Test the `/search/opening-hours` endpoint with local businesses in your area. Make sure the application correctly extracts and displays the opening hours.
   - If the pattern for extracting opening hours does not work well for businesses in your region, consider contributing by improving the regex pattern or extraction logic.

4. **Stock Price Retrieval**:
   - Test the stock price retrieval feature with companies listed on stock exchanges relevant to your region.
   - Suggest new companies and stock symbols to be added to the predefined `stock_name_to_symbol` dictionary in `app.py`.

### **How to Contribute**

1. **Fork the Repository**: Start by forking the repository to your GitHub account.
2. **Clone the Repository**: Clone the forked repository to your local machine.

    ```bash
    git clone https://github.com/yourusername/DuckDuckFind.git
    cd DuckDuckFind
    ```

3. **Create a New Branch**: Create a branch for your feature, bug fix, or testing contributions.

    ```bash
    git checkout -b my-new-feature
    ```

4. **Make Your Changes**: Implement your changes or run tests in the new branch. Ensure that your code adheres to the project's coding standards and conventions.

5. **Commit Your Changes**: After making your changes, commit them to the branch.

    ```bash
    git commit -m "Add new feature / Improve tests for region-specific functionality"
    ```

6. **Push to GitHub**: Push your branch to your forked repository on GitHub.

    ```bash
    git push origin my-new-feature
    ```

7. **Submit a Pull Request (PR)**: Open a pull request to the main repository. Provide a clear and concise description of your changes, or the results of your testing in different languages or regions. If your PR addresses a specific issue, please reference the issue number.

### **Code Review**

Once you've submitted a pull request, your code will be reviewed by the maintainers. They may request changes or improvements before your code is merged into the main branch. Please be open to feedback and respond to any comments or questions in a timely manner.

### **Suggestions and Feedback**

If you have suggestions on how to improve the application or encounter any issues, please open an issue on the GitHub repository. Include details about the language, region, or specific scenario where you encountered the issue.

### **Contributing Documentation**

If you would like to contribute to the project's documentation, you are more than welcome to do so. Documentation is just as important as the code itself, and we appreciate any improvements or additions you can make.

### **Community Guidelines**

We aim to foster a welcoming and inclusive environment. Please be respectful to other contributors and adhere to the [Code of Conduct](CODE_OF_CONDUCT.md) when interacting within the project.

### **🎈 Thank You 🎈**

Thank you for contributing to DuckDuckFind! ❤️🦆


## **Questions?**
