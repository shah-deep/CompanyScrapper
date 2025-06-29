from bs4 import BeautifulSoup
import requests
import time
import re
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque
import random
from .config import USER_AGENTS, BLOG_KEYWORDS, MAX_PAGES_PER_DOMAIN, REQUEST_DELAY, TIMEOUT, SKIP_URL_WORDS
import validators

class WebCrawler:
    def __init__(self, custom_skip_words=None):
        self.visited_urls = set()
        self.found_urls = []
        self.blog_urls = []
        self.company_name = None
        self.company_url = None
        self.skip_words = SKIP_URL_WORDS + (custom_skip_words or [])
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL to handle trailing slashes consistently."""
        if not url:
            return url
        
        # Parse the URL
        parsed = urlparse(url)
        
        # Normalize the path - remove trailing slash unless it's the root path
        path = parsed.path
        if path.endswith('/') and len(path) > 1:
            path = path.rstrip('/')
        
        # Reconstruct the URL
        normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        if parsed.fragment:
            normalized += f"#{parsed.fragment}"
        
        return normalized
        
    def set_company_info(self, company_name, company_url):
        """Set company information for URL filtering"""
        self.company_name = company_name
        self.company_url = company_url
    
    def should_skip_url(self, url):
        """Check if URL should be skipped based on skip words, but preserve if word is in company name or URL"""
        if not self.company_name or not self.company_url:
            return False
        
        url_lower = url.lower()
        company_name_lower = self.company_name.lower()
        company_url_lower = self.company_url.lower()
        
        for skip_word in self.skip_words:
            skip_word_lower = skip_word.lower()
            
            # Check if skip word is in the URL
            if skip_word_lower in url_lower:
                # But don't skip if the word is part of the company name
                if skip_word_lower in company_name_lower:
                    continue
                
                # Or if the word is part of the company URL
                if skip_word_lower in company_url_lower:
                    continue
                
                # Skip this URL
                return True
        
        return False
    
    def is_same_domain(self, url, base_url):
        """Check if URL belongs to the same domain as base URL"""
        try:
            base_domain = urlparse(base_url).netloc
            url_domain = urlparse(url).netloc
            return base_domain == url_domain
        except:
            return False
    
    def is_valid_url(self, url):
        """Validate URL format"""
        try:
            return validators.url(url) and not url.startswith(('mailto:', 'tel:', 'javascript:'))
        except:
            return False
    
    def is_blog_page(self, url, title, content):
        """Check if page is likely a blog post"""
        url_lower = url.lower()
        title_lower = title.lower() if title else ""
        content_lower = content.lower() if content else ""
        
        # Check URL for blog keywords
        for keyword in BLOG_KEYWORDS:
            if keyword in url_lower:
                return True
        
        # Check title for blog keywords
        for keyword in BLOG_KEYWORDS:
            if keyword in title_lower:
                return True
        
        # Check content for blog indicators
        blog_indicators = ['published', 'author', 'date', 'read more', 'continue reading']
        for indicator in blog_indicators:
            if indicator in content_lower:
                return True
        
        return False
    
    def get_page_links(self, url):
        """Extract all links from a webpage"""
        try:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get page title and content
            title = soup.title.string if soup.title else ""
            content = soup.get_text()[:1000] if soup.get_text() else ""
            
            # Check if this is a blog page
            if self.is_blog_page(url, title, content):
                self.blog_urls.append({
                    'url': url,
                    'title': title,
                    'type': 'blog'
                })
            
            # Extract all links
            links = []
            for link in soup.find_all('a', href=True):
                try:
                    href = link.get('href', '')  # type: ignore
                    if href and isinstance(href, str):
                        absolute_url = urljoin(url, href)
                        absolute_url, _ = urldefrag(absolute_url)  # Remove fragments
                        
                        if self.is_valid_url(absolute_url):
                            # Apply URL filtering
                            if not self.should_skip_url(absolute_url):
                                links.append(absolute_url)
                            else:
                                print(f"Skipping URL due to filter: {absolute_url}")
                except (AttributeError, TypeError):
                    continue
            
            return links, title, content
            
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return [], "", ""
    
    def crawl_company_site(self, start_url, max_pages=None):
        """Crawl company website to find all pages and blogs"""
        if max_pages is None:
            max_pages = MAX_PAGES_PER_DOMAIN
        
        print(f"Starting crawl of company site: {start_url}")
        
        queue = deque([start_url])
        self.visited_urls = set()
        self.found_urls = []
        self.blog_urls = []
        
        while queue and len(self.found_urls) < max_pages:
            current_url = queue.popleft()
            
            # Use normalized URL for visited check
            normalized_current_url = self._normalize_url(current_url)
            if normalized_current_url in self.visited_urls:
                continue
            
            self.visited_urls.add(normalized_current_url)
            
            # Only crawl URLs from the same domain
            if not self.is_same_domain(current_url, start_url):
                continue
            
            print(f"Crawling: {current_url}")
            
            links, title, content = self.get_page_links(current_url)
            
            # Add current URL to found URLs
            self.found_urls.append({
                'url': current_url,
                'title': title,
                'type': 'page'
            })
            
            # Add new links to queue (using normalized URLs for deduplication)
            seen_normalized = {self._normalize_url(link) for link in queue}
            for link in links:
                normalized_link = self._normalize_url(link)
                if (normalized_link not in self.visited_urls and 
                    normalized_link not in seen_normalized and
                    self.is_same_domain(link, start_url) and
                    len(self.found_urls) < max_pages):
                    queue.append(link)
                    seen_normalized.add(normalized_link)
            
            # Respect rate limiting
            time.sleep(REQUEST_DELAY)
        
        print(f"Crawl completed. Found {len(self.found_urls)} pages and {len(self.blog_urls)} blog posts.")
        return self.found_urls, self.blog_urls 