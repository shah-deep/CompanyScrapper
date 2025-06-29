import requests
from googleapiclient.discovery import build
import time
import random
from urllib.parse import urlparse
from config import GOOGLE_API_KEY, GOOGLE_CSE_ID, USER_AGENTS, FOUNDER_KEYWORDS

class BlogDiscovery:
    def __init__(self):
        self.google_service = None
        if GOOGLE_API_KEY and GOOGLE_CSE_ID:
            try:
                self.google_service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
            except Exception as e:
                print(f"Error initializing Google Search API: {str(e)}")
    
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
    
    def search_company_mentions(self, company_name):
        """Search for external mentions and articles about the company"""
        print(f"Searching for external mentions of {company_name}")
        
        external_mentions = []
        
        if not self.google_service:
            print("Google Search API not available. Skipping external mentions search.")
            return external_mentions
        
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
                    
                    # Validate if this is a relevant mention
                    if self._validate_company_mention(url, title, snippet, company_name):
                        external_mentions.append({
                            'url': url,
                            'title': title,
                            'source': 'google_search',
                            'type': 'external_mention'
                        })
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"Error searching for company mentions: {str(e)}")
                continue
        
        print(f"Found {len(external_mentions)} external mentions")
        return external_mentions
    
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
        news_indicators = ['news', 'article', 'press', 'interview', 'review', 'analysis', 'report']
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