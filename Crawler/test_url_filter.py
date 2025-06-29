#!/usr/bin/env python3
"""
Test script for URL filtering functionality
"""

from web_crawler import WebCrawler
from blog_discovery import BlogDiscovery
from founder_discovery import FounderDiscovery
from config import SKIP_URL_WORDS

def test_url_filtering():
    """Test URL filtering with various scenarios"""
    
    # Test case 1: Company with "reddit" in name should not skip reddit URLs
    print("Test 1: Company with 'reddit' in name")
    crawler = WebCrawler()
    crawler.set_company_info("Reddit Analytics", "https://redditanalytics.com")
    
    test_urls = [
        "https://reddit.com/r/python",
        "https://redditanalytics.com/blog",
        "https://facebook.com/redditanalytics",
        "https://twitter.com/redditanalytics"
    ]
    
    for url in test_urls:
        should_skip = crawler.should_skip_url(url)
        print(f"  {url}: {'SKIP' if should_skip else 'KEEP'}")
    
    print()
    
    # Test case 2: Regular company should skip reddit URLs
    print("Test 2: Regular company")
    crawler2 = WebCrawler()
    crawler2.set_company_info("TechCorp", "https://techcorp.com")
    
    test_urls2 = [
        "https://reddit.com/r/techcorp",
        "https://techcorp.com/blog",
        "https://facebook.com/techcorp",
        "https://twitter.com/techcorp"
    ]
    
    for url in test_urls2:
        should_skip = crawler2.should_skip_url(url)
        print(f"  {url}: {'SKIP' if should_skip else 'KEEP'}")
    
    print()
    
    # Test case 3: Custom skip words
    print("Test 3: Custom skip words")
    crawler3 = WebCrawler(custom_skip_words=["customsite", "testplatform"])
    crawler3.set_company_info("MyCompany", "https://mycompany.com")
    
    test_urls3 = [
        "https://customsite.com/mycompany",
        "https://testplatform.com/mycompany",
        "https://mycompany.com/blog",
        "https://reddit.com/r/mycompany"
    ]
    
    for url in test_urls3:
        should_skip = crawler3.should_skip_url(url)
        print(f"  {url}: {'SKIP' if should_skip else 'KEEP'}")
    
    print()
    
    # Test case 4: Company with skip word in URL
    print("Test 4: Company with skip word in URL")
    crawler4 = WebCrawler()
    crawler4.set_company_info("Facebook Analytics", "https://facebookanalytics.com")
    
    test_urls4 = [
        "https://facebook.com/facebookanalytics",
        "https://facebookanalytics.com/blog",
        "https://twitter.com/facebookanalytics"
    ]
    
    for url in test_urls4:
        should_skip = crawler4.should_skip_url(url)
        print(f"  {url}: {'SKIP' if should_skip else 'KEEP'}")

if __name__ == "__main__":
    print("Testing URL Filtering Functionality")
    print("=" * 50)
    test_url_filtering()
    print("\nTest completed!") 