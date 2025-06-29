import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from urllib.parse import urljoin, urlparse
import json
from config import GEMINI_API_KEY, USER_AGENTS
import random
import time

class CompanyExtractor:
    def __init__(self):
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)  # type: ignore
            self.model = genai.GenerativeModel('gemini-pro')  # type: ignore
        else:
            self.model = None
    
    def get_page_content(self, url):
        """Fetch and parse webpage content"""
        try:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text content
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return {
                'title': soup.title.string if soup.title else '',
                'text': text[:5000],  # Limit text for LLM processing
                'html': str(soup),
                'url': url
            }
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None
    
    def extract_company_info(self, url):
        """Extract company information using LLM"""
        print(f"Extracting company information from: {url}")
        
        page_data = self.get_page_content(url)
        if not page_data:
            return None
        
        if not self.model:
            # Fallback to basic extraction without LLM
            return self._basic_extraction(page_data)
        
        try:
            prompt = f"""
            Extract company information from this webpage. Return a JSON object with the following structure:
            {{
                "name": "Company name",
                "description": "Brief company description",
                "industry": "Industry/sector",
                "founded": "Year founded (if available)",
                "location": "Location/headquarters",
                "website": "Main website URL",
                "founders": ["List of founder names if available"],
                "key_people": ["List of key executives/leaders"],
                "products_services": ["List of main products or services"],
                "social_media": {{
                    "linkedin": "LinkedIn URL if available",
                    "twitter": "Twitter/X URL if available",
                    "facebook": "Facebook URL if available"
                }}
            }}
            
            Webpage title: {page_data['title']}
            Webpage content: {page_data['text'][:3000]}
            
            Return only the JSON object, no additional text.
            """
            
            response = self.model.generate_content(prompt)  # type: ignore
            company_info = json.loads(response.text)
            company_info['source_url'] = url
            
            return company_info
            
        except Exception as e:
            print(f"Error extracting company info with LLM: {str(e)}")
            return self._basic_extraction(page_data)
    
    def _basic_extraction(self, page_data):
        """Basic extraction without LLM"""
        soup = BeautifulSoup(page_data['html'], 'html.parser')
        
        # Extract basic info
        company_info = {
            'name': page_data['title'] or 'Unknown',
            'description': '',
            'industry': 'Unknown',
            'founded': 'Unknown',
            'location': 'Unknown',
            'website': page_data['url'],
            'founders': [],
            'key_people': [],
            'products_services': [],
            'social_media': {
                'linkedin': '',
                'twitter': '',
                'facebook': ''
            },
            'source_url': page_data['url']
        }
        
        # Try to find description in meta tags
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and hasattr(meta_desc, 'get'):
            company_info['description'] = meta_desc.get('content', '')  # type: ignore
        
        # Try to find social media links
        for link in soup.find_all('a', href=True):
            try:
                href = link.get('href', '')  # type: ignore
                if href and isinstance(href, str):
                    href_lower = href.lower()
                    if 'linkedin.com' in href_lower:
                        company_info['social_media']['linkedin'] = href
                    elif 'twitter.com' in href_lower or 'x.com' in href_lower:
                        company_info['social_media']['twitter'] = href
                    elif 'facebook.com' in href_lower:
                        company_info['social_media']['facebook'] = href
            except (AttributeError, TypeError):
                continue
        
        return company_info 