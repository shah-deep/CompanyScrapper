# Company Scraper

A comprehensive tool that analyzes a company's homepage, extracts company information, and discovers related URLs including blog posts, founder blogs, and external mentions.

## Features

- **Company Information Extraction**: Uses LLM (Gemini) to extract detailed company information from homepage
- **Founder Discovery**: Automatically searches for founders when not found during initial extraction
- **Website Crawling**: Discovers all pages and blog posts within the company's domain
- **Founder Blog Discovery**: Searches for blogs written by company founders
- **External Mentions**: Finds external articles and mentions about the company
- **Comprehensive Reporting**: Generates organized text files and JSON reports

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd CompanyScrapper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (optional but recommended):
Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_google_custom_search_engine_id
GEMINI_API_KEY=your_gemini_api_key
```

## API Setup

### Google Custom Search API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Custom Search API
4. Create credentials (API Key)
5. Go to [Google Custom Search](https://cse.google.com/)
6. Create a new search engine
7. Get your Search Engine ID (cx)

### Gemini API
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Add it to your `.env` file

## Usage

### Basic Usage
```bash
python main.py https://example.com
```

### Advanced Usage
```bash
# Crawl more pages
python main.py https://example.com --max-pages 100

# Generate simple URL list
python main.py https://example.com --simple

# Generate JSON report
python main.py https://example.com --json

# Skip external searches
python main.py https://example.com --skip-external --skip-founder-blogs

# Skip founder discovery search
python main.py https://example.com --skip-founder-search

# Custom output filename
python main.py https://example.com --output my_company_urls.txt
```

## Output Files

The tool generates several types of output files:

1. **Comprehensive URL List** (`company_name_urls_timestamp.txt`):
   - Organized sections for different URL types
   - Includes titles and metadata
   - Summary statistics

2. **Simple URL List** (`company_name_simple_urls_timestamp.txt`):
   - Just URLs, one per line
   - No duplicates
   - Easy to process

3. **JSON Report** (`company_name_report_timestamp.json`):
   - Complete data in JSON format
   - Includes company information and all URLs
   - Structured for programmatic access

## Project Structure

```
CompanyScrapper/
├── main.py                 # Main application entry point
├── config.py              # Configuration and settings
├── company_extractor.py   # Company information extraction
├── founder_discovery.py   # Founder discovery when not found initially
├── web_crawler.py         # Website crawling and blog discovery
├── blog_discovery.py      # Founder blog and external mention search
├── url_aggregator.py      # URL compilation and report generation
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── .env                  # Environment variables (create this)
```

## Configuration

Key configuration options in `config.py`:

- `MAX_PAGES_PER_DOMAIN`: Maximum pages to crawl (default: 50)
- `REQUEST_DELAY`: Delay between requests in seconds (default: 1)
- `TIMEOUT`: Request timeout in seconds (default: 30)
- `BLOG_KEYWORDS`: Keywords to identify blog pages
- `FOUNDER_KEYWORDS`: Keywords to identify founder-related content

## Features in Detail

### Company Information Extraction
- Extracts company name, description, industry, location
- Identifies founders and key people
- Finds social media links
- Uses LLM for intelligent extraction (fallback to basic extraction if no API)

### Founder Discovery
- Automatically searches for founders when not found during initial extraction
- Searches company website for founder information
- Uses Google Search to find founder mentions
- Searches professional networks (LinkedIn, Crunchbase, etc.)
- Extracts names using intelligent text parsing

### Website Crawling
- Crawls all pages within the company domain
- Identifies blog posts using keyword matching
- Respects robots.txt and rate limiting
- Handles relative and absolute URLs

### Founder Blog Discovery
- Searches for blogs written by company founders
- Uses Google Custom Search API
- Validates results for relevance
- Searches multiple platforms (Medium, Substack, LinkedIn, etc.)

### External Mentions
- Finds external articles about the company
- Excludes company's own domain
- Validates relevance using keyword matching
- Provides diverse sources of information

## Error Handling

The tool includes comprehensive error handling:
- Graceful handling of network errors
- Fallback mechanisms when APIs are unavailable
- Rate limiting to avoid being blocked
- Validation of URLs and data

## Limitations

- Requires Google APIs for full functionality
- Rate limited by external services
- May not find all blogs due to search limitations
- Depends on website structure for crawling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the documentation
2. Review the configuration
3. Ensure APIs are properly set up
4. Create an issue with detailed information 