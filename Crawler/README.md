# Company Scraper - Crawler Module

This module provides comprehensive company information extraction and URL discovery capabilities.

## Features

- **Company Information Extraction**: Extract company details using LLM
- **Website Crawling**: Discover all pages and blog posts on company websites
- **Founder Discovery**: Find company founders through web search with early termination
- **Blog Discovery**: Find blogs written by company founders
- **External Mentions**: Discover external articles and mentions about the company
- **URL Filtering**: Skip certain URLs while preserving company-related content
- **Early Termination**: Stop searching once founders are found to improve efficiency

## URL Filtering

The scraper includes intelligent URL filtering that skips certain domains/words while ensuring those words aren't in the company name or URL.

### Default Skip Words

The following words are automatically skipped when found in external URLs:
- Social media: reddit, facebook, twitter, instagram, tiktok, youtube, linkedin, pinterest, snapchat, whatsapp, telegram
- Communication: discord, slack, zoom, teams, meetup, eventbrite
- E-commerce: amazon, ebay, etsy, shopify, walmart, target, craigslist, kijiji, gumtree, offerup, letgo
- Reviews: yelp, tripadvisor, booking, airbnb, uber, lyft, doordash, grubhub, ubereats, postmates
- Search engines: google, bing, yahoo, duckduckgo, baidu
- Knowledge: wikipedia, wikihow, quora, stackoverflow, github, gitlab, bitbucket
- Tech platforms: docker, kubernetes, aws, azure, gcp, heroku, netlify, vercel, wordpress, wix, squarespace, magento, woocommerce

### Smart Filtering Logic

The filter preserves URLs if the skip word is part of:
- The company name (e.g., "Reddit Analytics" company won't skip reddit.com URLs)
- The company URL (e.g., "facebookanalytics.com" won't skip facebook.com URLs)

### Custom Skip Words

You can specify additional words to skip using the `--skip-words` argument:

```bash
python main.py https://company.com --skip-words reddit facebook twitter
```

## Usage

```bash
# Basic usage
python main.py https://example.com

# With custom skip words
python main.py https://company.com --skip-words reddit facebook

# Generate simple URL list
python main.py https://company.com --simple

# Generate JSON report
python main.py https://company.com --json

# Skip external searches
python main.py https://company.com --skip-external --skip-founder-blogs
```

## Configuration

Edit `config.py` to modify:
- Default skip words (`SKIP_URL_WORDS`)
- API keys and settings
- Crawling parameters
- User agents

## Output

The scraper generates:
- Comprehensive URL list with categories
- Simple URL list (just URLs)
- JSON report with all data
- Summary statistics

All output files are saved in the `data/scrapped_urls/` directory.

## Early Termination

The scraper implements intelligent early termination to improve efficiency:

### Founder Discovery Early Termination

- **Company Extraction**: If founders are found during initial company information extraction, the founder search step is skipped entirely
- **Web Search**: Once enough search results are collected (≥10 results), the system attempts to extract founders early instead of searching through all queries
- **Company Website**: When searching company website pages, the process stops as soon as founders are found on any page
- **Fallback Logic**: Only proceeds to fallback methods if no founders are found through primary methods

This ensures the scraper doesn't waste time on unnecessary searches when founders are already discovered. 