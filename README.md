# Company Crawler & Scrapper

[![Video Demo](https://img.shields.io/badge/Watch%20Demo-YouTube-red?logo=youtube)](https://youtu.be/o__WmIZd0x8)

A modern application to discover, crawl, and extract structured knowledge from company websites. It provides a user-friendly web interface for extracting company information, discovering related URLs, blogs, and technical content, and organizing the results for further analysis.

## Features
- **Company Crawler**: Crawls a company website to find all internal pages, blogs, and related URLs.
- **Company Info Extraction**: Extracts company name, description, industry, founders, key people, and social media links using LLMs or fallback methods.
- **Founder Discovery**: Finds founders via web search and on-site analysis.
- **Blog & External Mention Discovery**: Identifies blog posts, founder blogs, and external mentions using Google Search API and LLMs.
- **Knowledge Scrapper**: Scrapes and processes technical content from discovered URLs, supporting HTML, PDF, and plain text.
- **Database Integration**: Stores extracted knowledge in a MongoDB database for search and statistics.
- **Modern Web UI**: Elegant Flask-based interface for running crawls, scrapes, and viewing results.

## How to Run (Web UI)
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r UI/requirements.txt
   ```
2. Start the UI:
   ```bash
   python UI/run_ui.py
   ```
3. Open [http://localhost:5000](http://localhost:5000) in your browser.

## Environment Variables (.env)
Create a `.env` file in the project root with the following variables for full functionality:

```
# API Keys
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_google_cse_id
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash-lite

# MongoDB Configuration
MONGODB_URI=your_mongodb_uri
MONGODB_DATABASE=knowledgebase
MONGODB_COLLECTION=items

# Web Scraping Configuration
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# Content Processing
MAX_CONTENT_LENGTH=100000

# File Paths
OUTPUT_DIR=output
LOG_FILE=scrapper.log
```

---

**Note:**
- For advanced features (founder/blog discovery, LLM extraction), the API keys above are required.
- MongoDB is required for knowledge storage. 