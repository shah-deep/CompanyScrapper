import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Crawling Configuration
MAX_PAGES_PER_DOMAIN = 50
MAX_DEPTH = 3
REQUEST_DELAY = 1  # seconds between requests
TIMEOUT = 30  # seconds

# User Agents for web scraping
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

# Blog keywords to identify blog pages
BLOG_KEYWORDS = [
    'blog', 'news', 'articles', 'insights', 'thoughts', 'updates',
    'press', 'media', 'stories', 'journal', 'diary', 'notes'
]

# Founder-related keywords
FOUNDER_KEYWORDS = [
    'founder', 'co-founder', 'ceo', 'cto', 'coo', 'president',
    'director', 'executive', 'leadership', 'team', 'about'
] 