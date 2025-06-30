import requests
from googleapiclient.discovery import build
import time
import random
from urllib.parse import urlparse
from .config import GOOGLE_API_KEY, GOOGLE_CSE_ID, USER_AGENTS, FOUNDER_KEYWORDS, GEMINI_API_KEY, GEMINI_MODEL, SKIP_URL_WORDS
import google.generativeai as genai
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class BlogDiscovery:
    def __init__(self, custom_skip_words=None):
        self.google_service = None
        if GOOGLE_API_KEY and GOOGLE_CSE_ID:
            try:
                self.google_service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
            except Exception as e:
                print(f"Error initializing Google Search API: {str(e)}")
        
        # Initialize LLM for URL validation
        self.llm = None
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)  # type: ignore
                self.llm = genai.GenerativeModel(GEMINI_MODEL)  # type: ignore
            except Exception as e:
                print(f"Error initializing LLM for URL validation: {str(e)}")
                self.llm = None
        
        # Thread lock for LLM calls
        self.llm_lock = threading.Lock()
        self.llm_semaphore = threading.Semaphore(5)
        
        # Company info for URL filtering
        self.company_name = None
        self.company_url = None
        self.skip_words = SKIP_URL_WORDS + (custom_skip_words or [])
    
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
    
    def search_founder_blogs(self, company_name, founders):
        """Search for blogs written by company founders"""
        print(f"Searching for blogs by founders of {company_name}")
        
        founder_blogs = []
        
        if not self.google_service:
            print("Google Search API not available. Skipping founder blog search.")
            return founder_blogs
        
        for founder in founders:
            if not founder or founder.lower() in ['unknown', 'n/a', '']:
                continue
                
            print(f"Searching for blogs by: {founder}")
            
            # Search queries for founder blogs
            search_queries = [
                f'"{founder}" blog',
                f'"{founder}" "{company_name}" blog',
                f'"{founder}" author blog',
                f'"{founder}" medium.com',
                f'"{founder}" substack.com',
                f'"{founder}" linkedin.com posts',
                f'"{founder}" twitter.com blog',
                f'"{founder}" personal blog'
            ]
            
            for query in search_queries:
                try:
                    results = self._google_search(query, max_results=5)
                    
                    for result in results:
                        url = result.get('link', '')
                        title = result.get('title', '')
                        snippet = result.get('snippet', '')
                        
                        # Apply URL filtering
                        if self.should_skip_url(url):
                            print(f"Skipping founder blog URL due to filter: {url}")
                            continue
                        
                        # Validate if this is likely a blog by the founder
                        if self._validate_founder_blog(url, title, snippet, founder, company_name):
                            founder_blogs.append({
                                'url': url,
                                'title': title,
                                'founder': founder,
                                'source': 'google_search',
                                'type': 'founder_blog'
                            })
                    
                    # Rate limiting
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"Error searching for {founder}: {str(e)}")
                    continue
        
        print(f"Found {len(founder_blogs)} potential founder blogs")
        return founder_blogs
    
    def search_company_mentions(self, company_name, company_info=None):
        """Search for external mentions and articles about the company with LLM validation"""
        print(f"Searching for external mentions of {company_name}")
        
        # Step 1: Collect all potential external URLs
        potential_urls = []
        
        if not self.google_service:
            print("Google Search API not available. Skipping external mentions search.")
            return [], []
        
        # Search queries for company mentions
        search_queries = [
            f'"{company_name}" news',
            f'"{company_name}" article',
            f'"{company_name}" press release',
            f'"{company_name}" interview',
            f'"{company_name}" review',
            f'"{company_name}" analysis'
        ]
        
        for query in search_queries:
            try:
                results = self._google_search(query, max_results=10)
                
                for result in results:
                    url = result.get('link', '')
                    title = result.get('title', '')
                    snippet = result.get('snippet', '')
                    
                    # Skip if it's from the company's own domain
                    if self._is_company_domain(url, company_name):
                        continue
                    
                    # Apply URL filtering
                    if self.should_skip_url(url):
                        print(f"Skipping external mention URL due to filter: {url}")
                        continue
                    
                    # Basic validation - if it passes, add to potential URLs
                    if self._validate_company_mention(url, title, snippet, company_name):
                        potential_urls.append({
                            'url': url,
                            'title': title,
                            'snippet': snippet,
                            'source': 'google_search',
                            'type': 'external_mention'
                        })
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"Error searching for company mentions: {str(e)}")
                continue
        
        print(f"Found {len(potential_urls)} potential external mentions")
        
        # Step 2: LLM validation in parallel
        if self.llm and potential_urls:
            print("Validating URLs with LLM...")
            validated_urls, rejected_urls = self._validate_urls_with_llm(potential_urls, company_name, company_info)
        else:
            print("LLM not available, using basic validation only")
            validated_urls = potential_urls
            rejected_urls = []
        
        print(f"LLM validation results: {len(validated_urls)} validated, {len(rejected_urls)} potential")
        return validated_urls, rejected_urls
    
    def _google_search(self, query, max_results=10):
        """Perform Google Custom Search"""
        try:
            if not self.google_service:
                return []
                
            results = []
            for i in range(0, min(max_results, 10), 10):
                search_results = self.google_service.cse().list(
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

    def _google_search2(self, query, max_results=10):
        """Perform Google Custom Search"""
        try:
            if not self.google_service:
                return []
                
            results = []
            for i in range(0, max_results, 10):
                search_results = self.google_service.cse().list(
                    q=query,
                    cx=GOOGLE_CSE_ID,
                    start=i
                ).execute()
                
                if 'items' in search_results:
                    results.extend(search_results['items'])
                
                if len(results) >= max_results:
                    break
            
            return results[:max_results]
            
        except Exception as e:
            print(f"Google search error: {str(e)}")
            return []

    def _validate_founder_blog(self, url, title, snippet, founder, company_name):
        """Validate if a URL is likely a blog by the founder"""
        # Check if founder name appears in title or snippet
        founder_lower = founder.lower()
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        
        if founder_lower not in title_lower and founder_lower not in snippet_lower:
            return False
        
        # Check for blog indicators
        blog_indicators = ['blog', 'post', 'article', 'thoughts', 'insights', 'medium', 'substack']
        has_blog_indicator = any(indicator in title_lower or indicator in snippet_lower 
                               for indicator in blog_indicators)
        
        # Check for personal/author indicators
        author_indicators = ['author', 'written by', 'by ' + founder_lower]
        has_author_indicator = any(indicator in title_lower or indicator in snippet_lower 
                                 for indicator in author_indicators)
        
        return has_blog_indicator or has_author_indicator
    
    def _validate_company_mention(self, url, title, snippet, company_name):
        """Validate if a URL is a relevant mention of the company"""
        company_lower = company_name.lower()
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        
        # Company name should appear in title or snippet
        if company_lower not in title_lower and company_lower not in snippet_lower:
            return False
        
        # Check for news/article indicators
        news_indicators = ['news', 'article', 'press', 'interview', 'review', 'analysis']
        has_news_indicator = any(indicator in title_lower or indicator in snippet_lower 
                               for indicator in news_indicators)
        
        return has_news_indicator
    
    def _is_company_domain(self, url, company_name):
        """Check if URL is from the company's own domain"""
        try:
            domain = urlparse(url).netloc.lower()
            company_words = company_name.lower().split()
            
            # Check if any company word appears in domain
            for word in company_words:
                if len(word) > 2 and word in domain:
                    return True
            
            return False
        except:
            return False
    
    def _validate_urls_with_llm(self, potential_urls, company_name, company_info):
        """Validate URLs using LLM in parallel"""
        validated_urls = []
        rejected_urls = []
        
        if not self.llm:
            return potential_urls, []
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit validation tasks
            future_to_url = {
                executor.submit(self._validate_single_url_with_llm, url_data, company_name, company_info): url_data 
                for url_data in potential_urls
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_url):
                url_data = future_to_url[future]
                try:
                    is_valid = future.result()
                    if is_valid:
                        validated_urls.append(url_data)
                    else:
                        rejected_urls.append(url_data)
                except Exception as e:
                    print(f"Error validating URL {url_data.get('url', 'unknown')}: {str(e)}")
                    # If validation fails, treat as potential URL
                    rejected_urls.append(url_data)
        
        return validated_urls, rejected_urls
    
    def _validate_single_url_with_llm(self, url_data, company_name, company_info):
        """Validate a single URL using LLM with company context"""
        try:
            with self.llm_semaphore: #self.llm_lock:  # Ensure thread safety for LLM calls
                url = url_data.get('url', '')
                title = url_data.get('title', '')
                snippet = url_data.get('snippet', '')
                
                # Build company context information
                company_context = ""
                if company_info:
                    company_context = f"""
                Company Information:
                - Name: {company_info.get('name', company_name)}
                - Description: {company_info.get('description', 'N/A')}
                - Industry: {company_info.get('industry', 'N/A')}
                - Location: {company_info.get('location', 'N/A')}
                - Products/Services: {', '.join(company_info.get('products_services', []))}
                - Founders: {', '.join(company_info.get('founders', []))}
                """
                else:
                    company_context = f"Company: {company_name}"
                
                prompt = f"""
                Evaluate if this URL is a high-quality, relevant mention of the company.
                
                {company_context}
                
                URL to evaluate: {url}
                Title: {title}
                Snippet: {snippet}
                
                Consider the following criteria:
                1. Is this a legitimate news article, blog post, or professional content?
                2. Does it provide meaningful information about the company or its business?
                3. Is it from a reputable source (news sites, industry publications, etc.)?
                4. Is it recent and relevant to the company's current activities?
                5. Does it contain substantial content about the company (not just a brief mention)?
                6. Does it relate to the company's industry, products, services, or business activities?
                7. Is it likely to be useful for understanding the company's market presence, reputation, or business activities?
                
                Return only "YES" if the URL meets high-quality standards and is genuinely relevant to the company, or "NO" if it doesn't.
                """
                
                response = self.llm.generate_content(prompt)  # type: ignore
                response_text = response.text.strip().upper()
                
                # Add small delay to respect rate limits
                time.sleep(0.5)
                
                return response_text == "YES"
                
        except Exception as e:
            print(f"LLM validation error for {url_data.get('url', 'unknown')}: {str(e)}")
            return False
    
    def search_blog_subpages(self, base_blog_url, max_results=10):
        """Use Google Custom Search to find all URLs from the same domain as base_blog_url"""
        if not self.google_service:
            print("Google Search API not available. Skipping blog subpage search.")
            return []
        # Extract domain for site: operator
        print(f"Searching for blog subpages of {base_blog_url}")
        parsed = urlparse(base_blog_url)
        domain = parsed.netloc
        print(f"Domain: {domain}")
        # Build query: site:domain
        query = f"site:{domain} blog podcast post"
        print(f"Google searching for blog subpages with query: {query}")
        results = self._google_search2(query, max_results=max_results)
        # Filter URLs to only those that start with the base_blog_url
        matching_urls = []
        # print(f"Results: {results}")
        for result in results:
            url = result.get('link')
            if url:
                matching_urls.append(url)
        print(f"Found {len(matching_urls)} blog subpages via Google search.")
        return list(set(matching_urls)) 