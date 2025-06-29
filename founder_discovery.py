import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
import time
import random
from urllib.parse import urlparse
from config import GOOGLE_API_KEY, GOOGLE_CSE_ID, USER_AGENTS

class FounderDiscovery:
    def __init__(self):
        self.google_service = None
        if GOOGLE_API_KEY and GOOGLE_CSE_ID:
            try:
                self.google_service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
            except Exception as e:
                print(f"Error initializing Google Search API: {str(e)}")
    
    def search_founders(self, company_name, company_url):
        """Search for company founders when not found during initial extraction"""
        print(f"Searching for founders of {company_name}")
        
        founders = []
        
        # Method 1: Search company website for founder information
        website_founders = self._search_company_website(company_name, company_url)
        founders.extend(website_founders)
        
        # Method 2: Google search for founders
        if self.google_service:
            google_founders = self._google_search_founders(company_name)
            founders.extend(google_founders)
        
        # Method 3: Search LinkedIn and other professional networks
        professional_founders = self._search_professional_networks(company_name)
        founders.extend(professional_founders)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_founders = []
        for founder in founders:
            if founder.lower() not in seen:
                seen.add(founder.lower())
                unique_founders.append(founder)
        
        print(f"Found {len(unique_founders)} potential founders: {', '.join(unique_founders)}")
        return unique_founders
    
    def _search_company_website(self, company_name, company_url):
        """Search company website for founder information"""
        print(f"Searching company website for founders...")
        
        founders = []
        
        try:
            # Common founder page URLs
            founder_urls = [
                f"{company_url}/about",
                f"{company_url}/team",
                f"{company_url}/leadership",
                f"{company_url}/founders",
                f"{company_url}/about-us",
                f"{company_url}/our-team",
                f"{company_url}/company",
                f"{company_url}/who-we-are"
            ]
            
            for url in founder_urls:
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
                    
                    # Look for founder-related content
                    page_text = soup.get_text().lower()
                    
                    # Common founder indicators
                    founder_indicators = [
                        'founder', 'co-founder', 'ceo', 'cto', 'coo', 'president',
                        'chief executive', 'chief technology', 'chief operating'
                    ]
                    
                    if any(indicator in page_text for indicator in founder_indicators):
                        # Extract names near founder keywords
                        names = self._extract_names_near_keywords(soup, founder_indicators)
                        founders.extend(names)
                    
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    print(f"Error searching {url}: {str(e)}")
                    continue
            
        except Exception as e:
            print(f"Error searching company website: {str(e)}")
        
        return founders
    
    def _google_search_founders(self, company_name):
        """Search Google for company founders"""
        print(f"Searching Google for founders...")
        
        founders = []
        
        if not self.google_service:
            return founders
        
        search_queries = [
            f'"{company_name}" founders',
            f'"{company_name}" co-founders',
            f'"{company_name}" CEO founder',
            f'"{company_name}" who founded',
            f'"{company_name}" leadership team',
            f'"{company_name}" executive team'
        ]
        
        for query in search_queries:
            try:
                results = self._google_search(query, max_results=5)
                
                for result in results:
                    title = result.get('title', '')
                    snippet = result.get('snippet', '')
                    
                    # Extract names from search results
                    names = self._extract_names_from_text(title + ' ' + snippet)
                    founders.extend(names)
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                print(f"Error searching Google: {str(e)}")
                continue
        
        return founders
    
    def _search_professional_networks(self, company_name):
        """Search professional networks for founder information"""
        print(f"Searching professional networks...")
        
        founders = []
        
        if not self.google_service:
            return founders
        
        # Search LinkedIn and other professional sites
        search_queries = [
            f'"{company_name}" site:linkedin.com founders',
            f'"{company_name}" site:linkedin.com CEO',
            f'"{company_name}" site:crunchbase.com founders',
            f'"{company_name}" site:angel.co founders'
        ]
        
        for query in search_queries:
            try:
                results = self._google_search(query, max_results=3)
                
                for result in results:
                    title = result.get('title', '')
                    snippet = result.get('snippet', '')
                    
                    # Extract names from professional network results
                    names = self._extract_names_from_text(title + ' ' + snippet)
                    founders.extend(names)
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                print(f"Error searching professional networks: {str(e)}")
                continue
        
        return founders
    
    def _google_search(self, query, max_results=10):
        """Perform Google Custom Search"""
        try:
            if not self.google_service:
                return []
                
            results = []
            for i in range(0, min(max_results, 10), 10):
                search_results = self.google_service.list(
                    q=query,
                    cx=GOOGLE_CSE_ID,
                    start=i + 1
                ).execute()
                
                if 'items' in search_results:
                    results.extend(search_results['items'])
                
                if len(results) >= max_results:
                    break
            
            return results[:max_results]
            
        except Exception as e:
            print(f"Google search error: {str(e)}")
            return []
    
    def _extract_names_near_keywords(self, soup, keywords):
        """Extract names that appear near founder keywords"""
        names = []
        
        try:
            # Look for text containing founder keywords
            for keyword in keywords:
                # Find elements containing the keyword
                elements = soup.find_all(text=lambda text: text and keyword in text.lower())
                
                for element in elements:
                    # Get surrounding text
                    parent = element.parent
                    if parent:
                        text = parent.get_text()
                        # Extract potential names (simple heuristic)
                        potential_names = self._extract_names_from_text(text)
                        names.extend(potential_names)
            
        except Exception as e:
            print(f"Error extracting names: {str(e)}")
        
        return names
    
    def _extract_names_from_text(self, text):
        """Extract potential names from text (simple heuristic)"""
        names = []
        
        try:
            # Simple name extraction - look for capitalized words that might be names
            words = text.split()
            
            for i, word in enumerate(words):
                # Look for patterns like "John Smith" or "Dr. Jane Doe"
                if (word and word[0].isupper() and 
                    len(word) > 1 and 
                    not word.lower() in ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']):
                    
                    # Check if next word is also capitalized (potential last name)
                    if (i + 1 < len(words) and 
                        words[i + 1] and 
                        words[i + 1][0].isupper() and
                        len(words[i + 1]) > 1):
                        
                        full_name = f"{word} {words[i + 1]}"
                        if len(full_name) > 3 and full_name not in names:
                            names.append(full_name)
                    
                    # Single name (first name only)
                    elif len(word) > 2 and word not in names:
                        names.append(word)
            
        except Exception as e:
            print(f"Error extracting names from text: {str(e)}")
        
        return names[:10]  # Limit to 10 names to avoid spam 