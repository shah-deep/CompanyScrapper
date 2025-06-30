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
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
        
        # Enhanced tracking for iterative processing
        self.discovered_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        
        # Improved filtering patterns
        self.skip_patterns = [
            r'\.(doc|docx|xls|xlsx|ppt|pptx|zip|rar|jpg|jpeg|png|gif|svg|ico|css|js|xml|json|txt|csv)$',
            r'/(admin|login|logout|register|api|ajax|search|tag|category|author|user|profile)/',
            r'#.*$',  # Skip anchors
            r'\?(utm_|fbclid|gclid|ref=)',  # Skip tracking parameters
            r'/(privacy|terms|contact|about|help|support)/',  # Skip common non-content pages
            r'/(feed|rss|atom)/',  # Skip RSS feeds
            r'/(sitemap|robots)/',  # Skip sitemap and robots
        ]
    
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
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': Config.USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def discover_subpages(self, url: str) -> List[str]:
        """Discover subpages from a given URL with enhanced filtering."""
        if not self.session:
            self.logger.error("Session not initialized")
            return []
            
        try:
            self.logger.info(f"DISCOVER: {url}")
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.failed_urls.add(url)
                    self.logger.info(f"HTTP {response.status}: {url}")
                    return []
                
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    self.logger.info(f"SKIP {content_type}: {url}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find all links
                links = soup.find_all('a', href=True)
                
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
                
                # Remove duplicates using normalized URLs and return
                unique_subpages = []
                seen_normalized = set()
                for subpage in subpages:
                    normalized_url = self._normalize_url(subpage)
                    if normalized_url not in seen_normalized:
                        seen_normalized.add(normalized_url)
                        unique_subpages.append(subpage)
                
                self.discovered_urls.update(unique_subpages)
                self.logger.info(f"FOUND {len(unique_subpages)} subpages from {url}")
                return unique_subpages
                
        except Exception as e:
            self.logger.info(f"ERROR discovering {url}: {e}")
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