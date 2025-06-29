#!/usr/bin/env python3
"""
Integration Test for Company Crawler and Scrapper
Tests the complete flow from crawling to scraping
"""

import os
import sys
import time
from typing import Dict, Any

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the API modules
from Crawler.crawler_api import crawl_company, add_urls_to_existing_file, extract_urls_from_text
from Scrapper.scrapper_api import (
    scrape_company_knowledge, 
    search_company_knowledge, 
    get_company_knowledge_statistics,
    get_company_knowledge
)


def test_url_extraction():
    """Test URL extraction from text"""
    print("\n" + "="*60)
    print("TESTING URL EXTRACTION")
    print("="*60)
    
    # Test text with various URLs
    test_text = """
    Here are some URLs to test:
    https://example.com
    http://test.org/path?param=value
    https://blog.company.com/article-123
    https://github.com/user/repo
    https://medium.com/@author/post-title
    Invalid URL: not-a-url
    Another invalid: ftp://old-protocol.com
    """
    
    urls = extract_urls_from_text(test_text)
    
    print(f"Extracted URLs: {urls}")
    print(f"Total URLs found: {len(urls)}")
    
    expected_urls = {
        'https://example.com',
        'http://test.org/path?param=value',
        'https://blog.company.com/article-123',
        'https://github.com/user/repo',
        'https://medium.com/@author/post-title'
    }
    
    if urls == expected_urls:
        print("✅ URL extraction test PASSED")
        return True
    else:
        print("❌ URL extraction test FAILED")
        print(f"Expected: {expected_urls}")
        print(f"Got: {urls}")
        return False


def test_crawler_basic():
    """Test basic crawler functionality"""
    print("\n" + "="*60)
    print("TESTING BASIC CRAWLER")
    print("="*60)
    
    # Test with a simple company URL
    test_url = "https://example.com"
    
    try:
        result = crawl_company(
            company_url=test_url,
            max_pages=5,  # Limit for testing
            skip_external=True,  # Skip external search for testing
            skip_founder_blogs=True,  # Skip founder blogs for testing
            skip_founder_search=True,  # Skip founder search for testing
            simple_output=True
        )
        
        print(f"Crawler result: {result}")
        
        if result['success']:
            print("✅ Basic crawler test PASSED")
            return True
        else:
            print(f"❌ Basic crawler test FAILED: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Basic crawler test FAILED with exception: {str(e)}")
        return False


def test_crawler_with_additional_urls():
    """Test crawler with additional URLs"""
    print("\n" + "="*60)
    print("TESTING CRAWLER WITH ADDITIONAL URLS")
    print("="*60)
    
    test_url = "https://example.com"
    additional_urls = [
        "https://blog.example.com/post1",
        "https://docs.example.com/api",
        "https://github.com/example/repo"
    ]
    
    additional_text = """
    Here are some more URLs to add:
    https://medium.com/example/article
    https://stackoverflow.com/questions/example
    """
    
    try:
        result = crawl_company(
            company_url=test_url,
            additional_urls=additional_urls,
            additional_text=additional_text,
            max_pages=3,  # Limit for testing
            skip_external=True,
            skip_founder_blogs=True,
            skip_founder_search=True,
            simple_output=True
        )
        
        print(f"Crawler with additional URLs result: {result}")
        
        if result['success']:
            print("✅ Crawler with additional URLs test PASSED")
            return True
        else:
            print(f"❌ Crawler with additional URLs test FAILED: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Crawler with additional URLs test FAILED with exception: {str(e)}")
        return False


def test_add_urls_to_existing():
    """Test adding URLs to existing file"""
    print("\n" + "="*60)
    print("TESTING ADD URLS TO EXISTING FILE")
    print("="*60)
    
    test_url = "https://example.com"
    additional_urls = [
        "https://new-blog.example.com/post2",
        "https://new-docs.example.com/v2"
    ]
    
    additional_text = """
    More URLs to add:
    https://new-medium.example.com/article2
    """
    
    try:
        result = add_urls_to_existing_file(
            company_url=test_url,
            additional_urls=additional_urls,
            additional_text=additional_text
        )
        
        print(f"Add URLs result: {result}")
        
        if result['success']:
            print("✅ Add URLs to existing file test PASSED")
            return True
        else:
            print(f"❌ Add URLs to existing file test FAILED: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Add URLs to existing file test FAILED with exception: {str(e)}")
        return False


def test_scrapper_basic():
    """Test basic scrapper functionality"""
    print("\n" + "="*60)
    print("TESTING BASIC SCRAPPER")
    print("="*60)
    
    test_url = "https://example.com"
    team_id = "test_team_001"
    
    try:
        result = scrape_company_knowledge(
            company_url=test_url,
            team_id=team_id,
            processing_mode="multiprocessing",
            save_discovered_urls=True,
            iterative=False
        )
        
        print(f"Scrapper result: {result}")
        
        if result['success']:
            print("✅ Basic scrapper test PASSED")
            return True
        else:
            print(f"❌ Basic scrapper test FAILED: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Basic scrapper test FAILED with exception: {str(e)}")
        return False


def test_scrapper_search():
    """Test scrapper search functionality"""
    print("\n" + "="*60)
    print("TESTING SCRAPPER SEARCH")
    print("="*60)
    
    test_url = "https://example.com"
    team_id = "test_team_001"
    query = "test"
    
    try:
        result = search_company_knowledge(
            company_url=test_url,
            team_id=team_id,
            query=query
        )
        
        print(f"Search result: {result}")
        
        if result['success']:
            print("✅ Scrapper search test PASSED")
            return True
        else:
            print(f"❌ Scrapper search test FAILED: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Scrapper search test FAILED with exception: {str(e)}")
        return False


def test_scrapper_statistics():
    """Test scrapper statistics functionality"""
    print("\n" + "="*60)
    print("TESTING SCRAPPER STATISTICS")
    print("="*60)
    
    test_url = "https://example.com"
    team_id = "test_team_001"
    
    try:
        result = get_company_knowledge_statistics(
            company_url=test_url,
            team_id=team_id
        )
        
        print(f"Statistics result: {result}")
        
        if result['success']:
            print("✅ Scrapper statistics test PASSED")
            return True
        else:
            print(f"❌ Scrapper statistics test FAILED: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Scrapper statistics test FAILED with exception: {str(e)}")
        return False


def test_complete_flow():
    """Test the complete flow from crawling to scraping"""
    print("\n" + "="*60)
    print("TESTING COMPLETE FLOW")
    print("="*60)
    
    test_url = "https://example.com"
    team_id = "test_team_001"
    
    try:
        # Step 1: Crawl the company
        print("Step 1: Crawling company...")
        crawl_result = crawl_company(
            company_url=test_url,
            max_pages=3,
            skip_external=True,
            skip_founder_blogs=True,
            skip_founder_search=True,
            simple_output=True
        )
        
        if not crawl_result['success']:
            print(f"❌ Crawling failed: {crawl_result.get('error', 'Unknown error')}")
            return False
        
        print(f"✅ Crawling completed. Output file: {crawl_result['output_files'][0]}")
        
        # Step 2: Add some additional URLs
        print("\nStep 2: Adding additional URLs...")
        add_result = add_urls_to_existing_file(
            company_url=test_url,
            additional_urls=["https://blog.example.com/test-post"],
            additional_text="Check out this article: https://medium.com/example/test-article"
        )
        
        if add_result['success']:
            print(f"✅ Added {add_result.get('urls_added', 0)} new URLs")
        else:
            print(f"⚠️  Adding URLs failed: {add_result.get('error', 'Unknown error')}")
        
        # Step 3: Scrape knowledge
        print("\nStep 3: Scraping knowledge...")
        scrape_result = scrape_company_knowledge(
            company_url=test_url,
            team_id=team_id,
            processing_mode="multiprocessing",
            save_discovered_urls=True,
            iterative=False
        )
        
        if scrape_result['success']:
            print("✅ Knowledge scraping completed")
            stats = scrape_result['statistics']
            print(f"  - URLs processed: {stats.get('urls_processed', 0)}")
            print(f"  - URLs failed: {stats.get('urls_failed', 0)}")
            print(f"  - Knowledge items saved: {stats.get('knowledge_items_saved', 0)}")
        else:
            print(f"❌ Knowledge scraping failed: {scrape_result.get('error', 'Unknown error')}")
            return False
        
        # Step 4: Search knowledge
        print("\nStep 4: Searching knowledge...")
        search_result = search_company_knowledge(
            company_url=test_url,
            team_id=team_id,
            query="test"
        )
        
        if search_result['success']:
            print("✅ Knowledge search completed")
            results = search_result['results']
            print(f"  - Search results: {len(results)}")
        else:
            print(f"⚠️  Knowledge search failed: {search_result.get('error', 'Unknown error')}")
        
        # Step 5: Get statistics
        print("\nStep 5: Getting statistics...")
        stats_result = get_company_knowledge_statistics(
            company_url=test_url,
            team_id=team_id
        )
        
        if stats_result['success']:
            print("✅ Statistics retrieved")
            stats = stats_result['statistics']
            for key, value in stats.items():
                print(f"  - {key}: {value}")
        else:
            print(f"⚠️  Statistics retrieval failed: {stats_result.get('error', 'Unknown error')}")
        
        print("\n✅ Complete flow test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Complete flow test FAILED with exception: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("COMPANY CRAWLER & SCRAPPER INTEGRATION TESTS")
    print("="*80)
    
    test_results = []
    
    # Run individual tests
    test_results.append(("URL Extraction", test_url_extraction()))
    test_results.append(("Basic Crawler", test_crawler_basic()))
    test_results.append(("Crawler with Additional URLs", test_crawler_with_additional_urls()))
    test_results.append(("Add URLs to Existing File", test_add_urls_to_existing()))
    test_results.append(("Basic Scrapper", test_scrapper_basic()))
    test_results.append(("Scrapper Search", test_scrapper_search()))
    test_results.append(("Scrapper Statistics", test_scrapper_statistics()))
    
    # Run complete flow test
    test_results.append(("Complete Flow", test_complete_flow()))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
