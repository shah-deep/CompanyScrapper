import asyncio
import aiohttp
import PyPDF2
import io
import logging
from typing import Dict, Optional, Any
from bs4 import BeautifulSoup, Tag
import re

from config import Config

class ContentExtractor:
    def __init__(self):
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
    
    async def extract_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract content from a URL, handling different content types."""
        if not self.session:
            self.logger.error("Session not initialized")
            return None
            
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to fetch {url}: Status {response.status}")
                    return None
                
                content_type = response.headers.get('content-type', '').lower()
                
                if 'text/html' in content_type:
                    return await self._extract_html_content(url, response)
                elif 'application/pdf' in content_type:
                    return await self._extract_pdf_content(url, response)
                elif 'text/plain' in content_type:
                    return await self._extract_text_content(url, response)
                else:
                    self.logger.warning(f"Unsupported content type for {url}: {content_type}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    async def _extract_html_content(self, url: str, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Extract content from HTML pages."""
        html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract title
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
        
        # Extract main content
        content = ""
        
        # Try to find main content areas
        main_selectors = [
            'main',
            'article',
            '.content',
            '.post-content',
            '.entry-content',
            '#content',
            '#main',
            '.main-content'
        ]
        
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                content = main_content.get_text(separator='\n', strip=True)
                break
        
        # If no main content found, get body text
        if not content:
            body = soup.find('body')
            if body:
                content = body.get_text(separator='\n', strip=True)
        
        # Clean up content
        content = self._clean_text(content)
        
        # Extract author if possible
        author = self._extract_author(soup)
        
        return {
            'url': url,
            'title': title,
            'content': content,
            'author': author,
            'content_type': 'blog',
            'raw_html': html[:Config.MAX_CONTENT_LENGTH]  # Keep some raw HTML for context
        }
    
    async def _extract_pdf_content(self, url: str, response: aiohttp.ClientResponse) -> Optional[Dict[str, Any]]:
        """Extract content from PDF files."""
        try:
            pdf_data = await response.read()
            pdf_file = io.BytesIO(pdf_data)
            
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            title = ""
            content = ""
            
            # Try to extract title from metadata
            if pdf_reader.metadata:
                title = pdf_reader.metadata.get('/Title', '')
            
            # Extract text from all pages
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    content += page_text + "\n"
            
            # Clean up content
            content = self._clean_text(content)
            
            # If no title from metadata, try to extract from first page
            if not title and content:
                first_line = content.split('\n')[0].strip()
                if len(first_line) < 100:  # Reasonable title length
                    title = first_line
            
            return {
                'url': url,
                'title': title,
                'content': content,
                'author': '',  # PDFs don't typically have easily extractable authors
                'content_type': 'book',
                'raw_html': ''  # No HTML for PDFs
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting PDF content from {url}: {e}")
            return None
    
    async def _extract_text_content(self, url: str, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Extract content from plain text files."""
        content = await response.text()
        content = self._clean_text(content)
        
        # Try to extract title from first line
        lines = content.split('\n')
        title = lines[0].strip() if lines else ""
        
        return {
            'url': url,
            'title': title,
            'content': content,
            'author': '',
            'content_type': 'other',
            'raw_html': ''
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # Trim whitespace
        text = text.strip()
        
        # Limit content length
        if len(text) > Config.MAX_CONTENT_LENGTH:
            text = text[:Config.MAX_CONTENT_LENGTH] + "..."
        
        return text
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author information from HTML."""
        author_selectors = [
            '.author',
            '.byline',
            '.post-author',
            '.entry-author',
            '[rel="author"]',
            '.author-name',
            '.writer'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if isinstance(author_elem, Tag):
                author_text = author_elem.get_text().strip()
                if author_text:
                    return author_text
        
        # Try to find author in meta tags
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if isinstance(meta_author, Tag):
            content = meta_author.get('content', '')
            if isinstance(content, str):
                return content.strip()
        
        return ""

    def extract_content_sync(self, url: str) -> Optional[Dict[str, Any]]:
        """Synchronous version of extract_content for multiprocessing workers."""
        import asyncio
        
        # Create a new event loop for this thread/process
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(self.extract_content(url))
        finally:
            if loop.is_running():
                loop.close() 