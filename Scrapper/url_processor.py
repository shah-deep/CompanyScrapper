import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag
import logging
from typing import Set, List, Dict, Optional
import re

from config import Config

class URLProcessor:
    def __init__(self):
        self.processed_urls: Set[str] = set()
        self.url_queue: List[str] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
        
        # Enhanced tracking for iterative processing
        self.discovered_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        
        # Improved filtering patterns
        self.skip_patterns = [
            r'\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|jpg|jpeg|png|gif|svg|ico|css|js|xml|json|txt|csv)$',
            r'/(admin|login|logout|register|api|ajax|search|tag|category|author|user|profile)/',
            r'#.*$',  # Skip anchors
            r'\?(utm_|fbclid|gclid|ref=)',  # Skip tracking parameters
            r'/(privacy|terms|contact|about|help|support)/',  # Skip common non-content pages
            r'/(feed|rss|atom)/',  # Skip RSS feeds
            r'/(sitemap|robots)/',  # Skip sitemap and robots
        ]
        
        # Content type patterns to prioritize
        self.content_patterns = [
            r'/blog/',
            r'/article/',
            r'/post/',
            r'/guide/',
            r'/tutorial/',
            r'/docs/',
            r'/documentation/',
            r'/learn/',
            r'/resources/',
            r'/whitepaper/',
            r'/case-study/',
            r'/research/',
        ]
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': Config.USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def load_urls_from_file(self, file_path: str) -> List[str]:
        """Load URLs from a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                urls = [line.strip() for line in file if line.strip()]
            self.url_queue.extend(urls)
            self.logger.info(f"Loaded {len(urls)} URLs from {file_path}")
            return urls
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            return []
        except Exception as e:
            self.logger.error(f"Error loading URLs from file: {e}")
            return []
    
    def save_urls_to_file(self, file_path: str, urls: List[str]):
        """Save URLs to a text file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                for url in sorted(urls):
                    file.write(f"{url}\n")
            self.logger.info(f"Saved {len(urls)} URLs to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving URLs to file: {e}")
    
    def clear_state(self):
        """Clear all internal state for fresh iteration."""
        self.processed_urls.clear()
        self.url_queue.clear()
        self.discovered_urls.clear()
        self.failed_urls.clear()
    
    async def discover_subpages(self, url: str) -> List[str]:
        """Discover subpages from a given URL with enhanced filtering."""
        if not self.session:
            self.logger.error("Session not initialized")
            return []
            
        try:
            self.logger.info(f"Discovering subpages from: {url}")
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.failed_urls.add(url)
                    self.logger.warning(f"Failed to fetch {url}: Status {response.status}")
                    return []
                
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    self.logger.info(f"Skipping {url}: Not HTML content ({content_type})")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find all links
                links = soup.find_all('a', href=True)
                self.logger.info(f"Found {len(links)} total links on {url}")
                
                subpages = []
                filtered_count = 0
                
                base_url = url
                for link in links:
                    if isinstance(link, Tag):
                        href = link.get('href', '')
                        if href and isinstance(href, str):
                            absolute_url = urljoin(base_url, href)
                            
                            # Filter out external links and non-HTML content
                            if self._is_valid_subpage(absolute_url, base_url):
                                subpages.append(absolute_url)
                            else:
                                filtered_count += 1
                
                # Remove duplicates and return
                unique_subpages = list(set(subpages))
                self.discovered_urls.update(unique_subpages)
                self.logger.info(f"Discovered {len(unique_subpages)} subpages from {url} (filtered out {filtered_count} links)")
                return unique_subpages
                
        except Exception as e:
            self.logger.error(f"Error discovering subpages from {url}: {e}")
            self.failed_urls.add(url)
            return []
    
    def _is_valid_subpage(self, url: str, base_url: str) -> bool:
        """Check if a URL is a valid subpage with enhanced filtering."""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)
            
            # Must be same domain
            if parsed_url.netloc != parsed_base.netloc:
                return False
            
            # Must be HTTP/HTTPS
            if parsed_url.scheme not in ['http', 'https']:
                return False
            
            # Skip patterns that match skip_patterns (temporarily less restrictive for testing)
            for pattern in self.skip_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    # Log what's being filtered out for debugging
                    self.logger.debug(f"Filtered out URL: {url} (pattern: {pattern})")
                    return False
            
            # Additional validation (temporarily relaxed for testing)
            if len(url) > 1000:  # Increased from 500
                self.logger.debug(f"Filtered out URL: {url} (too long)")
                return False
            
            # Skip URLs with too many path segments (relaxed for testing)
            path_segments = [seg for seg in parsed_url.path.split('/') if seg]
            if len(path_segments) > 12:  # Increased from 8
                self.logger.debug(f"Filtered out URL: {url} (too many path segments)")
                return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Error validating URL {url}: {e}")
            return False
    
    def _is_content_page(self, url: str) -> bool:
        """Check if URL is likely a content page."""
        url_lower = url.lower()
        
        # Check for content patterns
        for pattern in self.content_patterns:
            if re.search(pattern, url_lower):
                return True
        
        # Check for date patterns (common in blog posts)
        date_patterns = [
            r'/\d{4}/\d{2}/',  # /2024/01/
            r'/\d{4}-\d{2}/',  # /2024-01/
            r'/\d{4}/\d{2}/\d{2}/',  # /2024/01/15/
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, url):
                return True
        
        return False
    
    def add_urls_to_queue(self, urls: List[str]):
        """Add new URLs to the processing queue with deduplication."""
        new_urls = []
        for url in urls:
            if (url not in self.processed_urls and 
                url not in self.url_queue and 
                url not in self.discovered_urls):
                new_urls.append(url)
        
        self.url_queue.extend(new_urls)
        self.discovered_urls.update(new_urls)
        self.logger.info(f"Added {len(new_urls)} new URLs to queue")
    
    def get_next_url(self) -> Optional[str]:
        """Get the next URL from the queue."""
        if self.url_queue:
            url = self.url_queue.pop(0)
            self.processed_urls.add(url)
            return url
        return None
    
    def mark_url_processed(self, url: str):
        """Mark a URL as processed."""
        self.processed_urls.add(url)
    
    def get_queue_status(self) -> Dict:
        """Get current queue status."""
        return {
            'queue_length': len(self.url_queue),
            'processed_count': len(self.processed_urls),
            'discovered_count': len(self.discovered_urls),
            'failed_count': len(self.failed_urls),
            'total_urls': len(self.url_queue) + len(self.processed_urls)
        }
    
    def get_discovered_urls(self) -> Set[str]:
        """Get all discovered URLs."""
        return self.discovered_urls.copy()
    
    def get_failed_urls(self) -> Set[str]:
        """Get all failed URLs."""
        return self.failed_urls.copy()
    
    def filter_content_urls(self, urls: List[str]) -> List[str]:
        """Filter URLs to prioritize content pages."""
        content_urls = []
        other_urls = []
        
        for url in urls:
            if self._is_content_page(url):
                content_urls.append(url)
            else:
                other_urls.append(url)
        
        # Return content URLs first, then others
        return content_urls + other_urls
    
    def discover_subpages_sync(self, url: str) -> List[str]:
        """Synchronous version of discover_subpages for multiprocessing workers."""
        import asyncio
        import aiohttp
        
        # Create a new event loop for this thread/process
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            # Create a new session for this process
            session = aiohttp.ClientSession(
                headers={'User-Agent': Config.USER_AGENT},
                timeout=aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT)
            )
            
            # Create a temporary processor with the session
            temp_processor = URLProcessor()
            temp_processor.session = session
            
            # Run the discovery
            result = loop.run_until_complete(temp_processor.discover_subpages(url))
            
            # Clean up session
            loop.run_until_complete(session.close())
            
            return result
        finally:
            if loop.is_running():
                loop.close() 