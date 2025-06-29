#!/usr/bin/env python3
"""
Basic test script to verify core functionality
Tests components without requiring API keys
"""

import sys
import os

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from config import USER_AGENTS, BLOG_KEYWORDS, FOUNDER_KEYWORDS
        print("✓ Config imported successfully")
    except ImportError as e:
        print(f"✗ Config import failed: {e}")
        return False
    
    try:
        from company_extractor import CompanyExtractor
        print("✓ CompanyExtractor imported successfully")
    except ImportError as e:
        print(f"✗ CompanyExtractor import failed: {e}")
        return False
    
    try:
        from web_crawler import WebCrawler
        print("✓ WebCrawler imported successfully")
    except ImportError as e:
        print(f"✗ WebCrawler import failed: {e}")
        return False
    
    try:
        from blog_discovery import BlogDiscovery
        print("✓ BlogDiscovery imported successfully")
    except ImportError as e:
        print(f"✗ BlogDiscovery import failed: {e}")
        return False
    
    try:
        from url_aggregator import URLAggregator
        print("✓ URLAggregator imported successfully")
    except ImportError as e:
        print(f"✗ URLAggregator import failed: {e}")
        return False
    
    return True

def test_components():
    """Test component initialization"""
    print("\nTesting component initialization...")
    
    try:
        from company_extractor import CompanyExtractor
        extractor = CompanyExtractor()
        print("✓ CompanyExtractor initialized")
    except Exception as e:
        print(f"✗ CompanyExtractor initialization failed: {e}")
        return False
    
    try:
        from web_crawler import WebCrawler
        crawler = WebCrawler()
        print("✓ WebCrawler initialized")
    except Exception as e:
        print(f"✗ WebCrawler initialization failed: {e}")
        return False
    
    try:
        from blog_discovery import BlogDiscovery
        blog_discovery = BlogDiscovery()
        print("✓ BlogDiscovery initialized")
    except Exception as e:
        print(f"✗ BlogDiscovery initialization failed: {e}")
        return False
    
    try:
        from url_aggregator import URLAggregator
        aggregator = URLAggregator()
        print("✓ URLAggregator initialized")
    except Exception as e:
        print(f"✗ URLAggregator initialization failed: {e}")
        return False
    
    return True

def test_url_aggregator():
    """Test URL aggregator functionality"""
    print("\nTesting URL aggregator...")
    
    try:
        from url_aggregator import URLAggregator
        
        aggregator = URLAggregator()
        
        # Test data
        test_pages = [
            {'url': 'https://example.com', 'title': 'Homepage', 'type': 'page'},
            {'url': 'https://example.com/about', 'title': 'About', 'type': 'page'}
        ]
        
        test_blogs = [
            {'url': 'https://example.com/blog', 'title': 'Blog', 'type': 'blog'}
        ]
        
        # Add data
        aggregator.add_company_pages(test_pages)
        aggregator.add_blog_posts(test_blogs)
        
        # Test summary
        total = aggregator.get_total_urls()
        if total == 3:
            print("✓ URL aggregator working correctly")
            return True
        else:
            print(f"✗ URL aggregator count mismatch: expected 3, got {total}")
            return False
            
    except Exception as e:
        print(f"✗ URL aggregator test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Company Scraper - Basic Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed")
        return False
    
    # Test component initialization
    if not test_components():
        print("\n❌ Component initialization tests failed")
        return False
    
    # Test URL aggregator
    if not test_url_aggregator():
        print("\n❌ URL aggregator tests failed")
        return False
    
    print("\n✅ All basic tests passed!")
    print("\nThe Company Scraper is ready to use.")
    print("To get full functionality, set up your API keys in a .env file:")
    print("  - GOOGLE_API_KEY")
    print("  - GOOGLE_CSE_ID") 
    print("  - GEMINI_API_KEY")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 