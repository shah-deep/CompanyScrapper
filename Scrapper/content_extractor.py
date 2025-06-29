import asyncio
import aiohttp
import PyPDF2
import io
import logging
from typing import Dict, Optional, Any, List
from bs4 import BeautifulSoup, Tag
import re
import json

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
            'content_type': 'blog'
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
                'content_type': 'book'
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
            'content_type': 'other'
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
        """Extract author information from HTML with enhanced patterns for multiple authors."""
        authors = set()  # Use set to avoid duplicates
        
        # Try all selectors for multiple authors
        author_selectors = [
            # Common author selectors
            '.author',
            '.byline',
            '.post-author',
            '.entry-author',
            '[rel="author"]',
            '.author-name',
            '.writer',
            '.contributor',
            '.staff-author',
            '.article-author',
            '.blog-author',
            '.content-author',
            
            # More specific selectors
            'span.author',
            'div.author',
            'p.author',
            '.meta .author',
            '.post-meta .author',
            '.entry-meta .author',
            '.article-meta .author',
            '.blog-meta .author',
            
            # Structured data patterns
            '[itemprop="author"]',
            '[data-author]',
            '.author-info',
            '.author-details',
            '.author-bio',
            '.author-profile',
            
            # Social media patterns
            '.twitter-handle',
            '.linkedin-profile',
            '.github-profile',
            
            # Publication patterns
            '.published-by',
            '.written-by',
            '.posted-by',
            '.created-by'
        ]
        
        # Try all selectors for multiple elements
        for selector in author_selectors:
            author_elements = soup.select(selector)  # Use select() instead of select_one()
            for author_elem in author_elements:
                if isinstance(author_elem, Tag):
                    author_text = author_elem.get_text().strip()
                    if author_text and len(author_text) > 0 and len(author_text) < 100:
                        # Clean up the author text
                        author_text = self._clean_author_text(author_text)
                        if author_text:
                            authors.add(author_text)
        
        # Try to find author in meta tags
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if isinstance(meta_author, Tag):
            content = meta_author.get('content', '')
            if isinstance(content, str) and content.strip():
                author_text = self._clean_author_text(content.strip())
                if author_text:
                    authors.add(author_text)
        
        # Try Open Graph author
        og_author = soup.find('meta', attrs={'property': 'article:author'})
        if isinstance(og_author, Tag):
            content = og_author.get('content', '')
            if isinstance(content, str) and content.strip():
                author_text = self._clean_author_text(content.strip())
                if author_text:
                    authors.add(author_text)
        
        # Try Twitter Card author
        twitter_author = soup.find('meta', attrs={'name': 'twitter:creator'})
        if isinstance(twitter_author, Tag):
            content = twitter_author.get('content', '')
            if isinstance(content, str) and content.strip():
                author_text = self._clean_author_text(content.strip())
                if author_text:
                    authors.add(author_text)
        
        # Try to find author in structured data (JSON-LD)
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                if isinstance(script, Tag) and script.string:
                    data = json.loads(script.string)
                    json_authors = self._extract_authors_from_json_ld(data)
                    for author in json_authors:
                        if author:
                            authors.add(author)
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
        
        # Try to find author in common text patterns
        author_patterns = [
            r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Author:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Written by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Posted by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Contributor:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        page_text = soup.get_text()
        for pattern in author_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                author_text = match.strip()
                if author_text and len(author_text) < 100:
                    author_text = self._clean_author_text(author_text)
                    if author_text:
                        authors.add(author_text)
        
        # Return comma-separated authors
        return ', '.join(sorted(authors)) if authors else ""
    
    def _clean_author_text(self, author_text: str) -> str:
        """Clean and normalize author text."""
        if not author_text:
            return ""
        
        # Remove common prefixes/suffixes
        author_text = re.sub(r'^(by|author|written by|posted by|contributor):\s*', '', author_text, flags=re.IGNORECASE)
        author_text = re.sub(r'\s+(on|at|in)\s+\d{4}.*$', '', author_text, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        author_text = re.sub(r'\s+', ' ', author_text).strip()
        
        # Remove very short or very long names
        if len(author_text) < 2 or len(author_text) > 100:
            return ""
        
        # Remove names that look like dates or other non-author text
        if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', author_text):
            return ""
        
        return author_text
    
    def _extract_authors_from_json_ld(self, data: Dict) -> List[str]:
        """Extract multiple authors from JSON-LD structured data."""
        authors = []
        
        try:
            # Handle different JSON-LD structures
            if isinstance(data, dict):
                # Direct author field (could be single or array)
                if 'author' in data:
                    author = data['author']
                    if isinstance(author, str):
                        authors.append(author)
                    elif isinstance(author, dict) and 'name' in author:
                        authors.append(author['name'])
                    elif isinstance(author, list):
                        for auth in author:
                            if isinstance(auth, str):
                                authors.append(auth)
                            elif isinstance(auth, dict) and 'name' in auth:
                                authors.append(auth['name'])
                
                # Article author
                if 'article' in data and isinstance(data['article'], dict):
                    article = data['article']
                    if 'author' in article:
                        author = article['author']
                        if isinstance(author, str):
                            authors.append(author)
                        elif isinstance(author, dict) and 'name' in author:
                            authors.append(author['name'])
                        elif isinstance(author, list):
                            for auth in author:
                                if isinstance(auth, str):
                                    authors.append(auth)
                                elif isinstance(auth, dict) and 'name' in auth:
                                    authors.append(auth['name'])
                
                # BlogPosting author
                if 'blogPosting' in data and isinstance(data['blogPosting'], dict):
                    blog_post = data['blogPosting']
                    if 'author' in blog_post:
                        author = blog_post['author']
                        if isinstance(author, str):
                            authors.append(author)
                        elif isinstance(author, dict) and 'name' in author:
                            authors.append(author['name'])
                        elif isinstance(author, list):
                            for auth in author:
                                if isinstance(auth, str):
                                    authors.append(auth)
                                elif isinstance(auth, dict) and 'name' in auth:
                                    authors.append(auth['name'])
                
                # Recursively search for authors in nested structures
                for key, value in data.items():
                    if isinstance(value, dict):
                        nested_authors = self._extract_authors_from_json_ld(value)
                        authors.extend(nested_authors)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                nested_authors = self._extract_authors_from_json_ld(item)
                                authors.extend(nested_authors)
            
            return authors
            
        except Exception:
            return []

    def extract_content_sync(self, url: str) -> Optional[Dict[str, Any]]:
        """Synchronous version of extract_content for multiprocessing workers."""
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
            
            # Create a temporary extractor with the session
            temp_extractor = ContentExtractor()
            temp_extractor.session = session
            
            # Run the extraction
            result = loop.run_until_complete(temp_extractor.extract_content(url))
            
            # Clean up session
            loop.run_until_complete(session.close())
            
            return result
        finally:
            if loop.is_running():
                loop.close() 