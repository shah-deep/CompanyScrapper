import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
import time
import random
from urllib.parse import urlparse
from config import GOOGLE_API_KEY, GOOGLE_CSE_ID, USER_AGENTS, GEMINI_API_KEY
import google.generativeai as genai
import json

class FounderDiscovery:
    def __init__(self):
        self.google_service = None
        if GOOGLE_API_KEY and GOOGLE_CSE_ID:
            try:
                self.google_service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
            except Exception as e:
                print(f"Error initializing Google Search API: {str(e)}")
                self.google_service = None
        
        # Initialize LLM for name extraction
        self.llm = None
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)  # type: ignore
                self.llm = genai.GenerativeModel('gemini-2.0-flash-lite')  # type: ignore
            except Exception as e:
                print(f"Error initializing LLM: {str(e)}")
                self.llm = None
    
    def search_founders(self, company_name, company_url):
        """Search for company founders using web search and LLM extraction"""
        print(f"Searching for founders of {company_name}")
        
        founders = []
        
        # Method 1: Web search for founders
        if self.google_service:
            web_founders = self._web_search_founders(company_name, company_url)
            founders.extend(web_founders)
        
        # Method 2: Search company website for founder information (fallback)
        if not founders:
            website_founders = self._search_company_website(company_name, company_url)
            founders.extend(website_founders)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_founders = []
        for founder in founders:
            if founder.lower() not in seen:
                seen.add(founder.lower())
                unique_founders.append(founder)
        
        print(f"Found {len(unique_founders)} potential founders: {', '.join(unique_founders)}")
        return unique_founders
    
    def _web_search_founders(self, company_name, company_url):
        """Search web for founders using Google and extract names with LLM"""
        print(f"Searching web for founders...")
        
        founders = []
        
        if not self.google_service or not self.llm:
            return founders
        
        # Search queries for founders
        search_queries = [
            f"Founders of {company_name}",
            f"Who founded {company_name}",
            f"{company_name} founders CEO",
            f"{company_name} co-founders",
            f"Who started {company_name}",
            f"{company_name} leadership team founders"
        ]
        
        all_search_results = []
        
        for query in search_queries:
            try:
                results = self._google_search(query, max_results=5)
                all_search_results.extend(results)
                time.sleep(2)  # Rate limiting
            except Exception as e:
                print(f"Error searching for '{query}': {str(e)}")
                continue
        
        if all_search_results:
            # Extract founder names using LLM
            founders = self._extract_founder_names_with_llm(company_name, all_search_results)
        
        return founders
    
    def _extract_founder_names_with_llm(self, company_name, search_results):
        """Use LLM to extract founder names from search results"""
        try:
            # Prepare search results text
            results_text = ""
            for i, result in enumerate(search_results[:10]):  # Limit to 10 results
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                results_text += f"Result {i+1}:\nTitle: {title}\nSnippet: {snippet}\n\n"
            
            prompt = f"""
            Extract founder names from these search results about {company_name}.
            
            Search Results:
            {results_text}
            
            Instructions:
            1. Look for people who are described as founders, co-founders, CEOs, or who started the company
            2. Extract full names (first and last name when possible)
            3. Return only a JSON array of founder names
            4. If no founders are found, return an empty array []
            5. Do not include titles like "CEO", "CTO", etc. - just names
            
            Return only the JSON array, no additional text.
            """
            
            response = self.llm.generate_content(prompt)  # type: ignore
            response_text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()
            
            # Parse JSON response
            try:
                founder_names = json.loads(response_text)
                if isinstance(founder_names, list):
                    return founder_names
                else:
                    print("LLM returned non-list response")
                    return []
            except json.JSONDecodeError:
                print("Error parsing LLM response as JSON")
                return []
                
        except Exception as e:
            print(f"Error extracting founder names with LLM: {str(e)}")
            return []
    
    def _google_search(self, query, max_results=10):
        """Perform Google Custom Search"""
        try:
            if not self.google_service:
                return []
                
            results = []
            for i in range(0, min(max_results, 10), 10):
                try:
                    search_results = self.google_service.cse().list(
                        q=query,
                        cx=GOOGLE_CSE_ID,
                        start=i + 1
                    ).execute()
                    
                    if 'items' in search_results:
                        results.extend(search_results['items'])
                    
                    if len(results) >= max_results:
                        break
                except Exception as e:
                    print(f"Google search error for query '{query}': {str(e)}")
                    break
            
            return results[:max_results]
            
        except Exception as e:
            print(f"Google search error: {str(e)}")
            return []
    
    def _search_company_website(self, company_name, company_url):
        """Search company website for founder information (fallback method)"""
        print(f"Searching company website for founders (fallback)...")
        
        founders = []
        
        try:
            # Ensure company_url doesn't end with slash
            base_url = company_url.rstrip('/')
            
            # Common founder page URLs
            founder_urls = [
                f"{base_url}/about",
                f"{base_url}/team",
                f"{base_url}/leadership",
                f"{base_url}/founders",
                f"{base_url}/about-us",
                f"{base_url}/our-team",
                f"{base_url}/company",
                f"{base_url}/who-we-are"
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