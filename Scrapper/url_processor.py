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
                for url in urls:
                    file.write(f"{url}\n")
            self.logger.info(f"Saved {len(urls)} URLs to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving URLs to file: {e}")
    
    async def discover_subpages(self, url: str) -> List[str]:
        """Discover subpages from a given URL."""
        if not self.session:
            self.logger.error("Session not initialized")
            return []
            
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return []
                
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find all links
                links = soup.find_all('a', href=True)
                subpages = []
                
                base_url = url
                for link in links:
                    if isinstance(link, Tag):
                        href = link.get('href', '')
                        if href and isinstance(href, str):
                            absolute_url = urljoin(base_url, href)
                            
                            # Filter out external links and non-HTML content
                            if self._is_valid_subpage(absolute_url, base_url):
                                subpages.append(absolute_url)
                
                # Remove duplicates and return
                unique_subpages = list(set(subpages))
                self.logger.info(f"Discovered {len(unique_subpages)} subpages from {url}")
                return unique_subpages
                
        except Exception as e:
            self.logger.error(f"Error discovering subpages from {url}: {e}")
            return []
    
    def _is_valid_subpage(self, url: str, base_url: str) -> bool:
        """Check if a URL is a valid subpage."""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)
            
            # Must be same domain
            if parsed_url.netloc != parsed_base.netloc:
                return False
            
            # Must be HTTP/HTTPS
            if parsed_url.scheme not in ['http', 'https']:
                return False
            
            # Skip common non-content paths
            skip_patterns = [
                r'\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|jpg|jpeg|png|gif|svg|ico|css|js|xml|json)$',
                r'/(admin|login|logout|register|api|ajax|search|tag|category|author)/',
                r'#.*$',  # Skip anchors
                r'\?.*$'  # Skip query parameters for now
            ]
            
            for pattern in skip_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def add_urls_to_queue(self, urls: List[str]):
        """Add new URLs to the processing queue."""
        new_urls = [url for url in urls if url not in self.processed_urls and url not in self.url_queue]
        self.url_queue.extend(new_urls)
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
            'total_urls': len(self.url_queue) + len(self.processed_urls)
        } 