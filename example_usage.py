#!/usr/bin/env python3
"""
Example Usage of Company Crawler and Scrapper APIs
Demonstrates how to use the new function-based interfaces
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the API modules
from Crawler.crawler_api import crawl_company, add_urls_to_existing_file, extract_urls_from_text
from Scrapper.scrapper_api import (
    scrape_company_knowledge, 
    search_company_knowledge, 
    get_company_knowledge_statistics
)


def example_crawler_usage():
    """Example of how to use the crawler API"""
    print("="*60)
    print("EXAMPLE: CRAWLER USAGE")
    print("="*60)
    
    
    # Example 1: Crawling with additional URLs
    print("\n2. Crawling with Additional URLs")
    print("-" * 40)
    
    additional_urls = [
        "https://blog.example.com/important-post",
        "https://docs.example.com/api-reference"
    ]
    
    additional_text = """
    Here are some more URLs to include:
    https://drive.google.com/file/d/10W-Wl8DMISmLe6z1GnTu09sEyuX9dnm6/view?usp=sharing

    """
    
    result = crawl_company(
        company_url="https://interviewing.io",
        additional_urls=additional_urls,
        additional_text=additional_text,
        max_pages=5,
        skip_external=True,
        skip_founder_blogs=True,
        skip_founder_search=True,
        simple_output=True
    )
    
    if result['success']:
        print(f"✅ Crawling with additional URLs completed!")
        print(f"   Additional URLs added: {result['summary']['additional_urls_added']}")
        print(f"   Total URLs: {result['summary']['total_unique_urls']}")
    
    # Example 3: Adding URLs to existing file
    print("\n3. Adding URLs to Existing File")
    print("-" * 40)
    
    add_result = add_urls_to_existing_file(
        company_url="https://interviewing.io",
        additional_urls=["https://new-blog.example.com/post"],
        additional_text="Check out this new article: https://medium.com/example/new-post"
    )
    
    if add_result['success']:
        print(f"✅ URLs added successfully!")
        print(f"   URLs added: {add_result.get('urls_added', 0)}")
        if add_result.get('new_urls'):
            print(f"   New URLs: {add_result['new_urls']}")
    else:
        print(f"❌ Adding URLs failed: {add_result.get('error', 'Unknown error')}")


def example_scrapper_usage():
    """Example of how to use the scrapper API"""
    print("\n" + "="*60)
    print("EXAMPLE: SCRAPPER USAGE")
    print("="*60)
    
    team_id = "example_team_001"
    company_url = "https://interviewing.io"
    
    
    # Example 1: Iterative knowledge scraping
    print("\n1. Iterative Knowledge Scraping")
    print("-" * 40)
    
    result = scrape_company_knowledge(
        company_url=company_url,
        team_id=team_id,
        processing_mode="multiprocessing",
        save_discovered_urls=True,
        iterative=False  # Use iterative subpage discovery
    )
    
    if result['success']:
        print(f"✅ Iterative knowledge scraping completed!")
        stats = result['statistics']
        print(f"   Iterations completed: {stats.get('iterations_completed', 0)}")
        print(f"   Total new links found: {stats.get('total_new_links_found', 0)}")
        print(f"   Knowledge items saved: {stats.get('knowledge_items_saved', 0)}")
    
    '''
    # Example 2: Searching knowledge
    print("\n2. Searching Knowledge")
    print("-" * 40)
    
    search_result = search_company_knowledge(
        company_url=company_url,
        team_id=team_id,
        query="API documentation"
    )
    
    if search_result['success']:
        print(f"✅ Knowledge search completed!")
        results = search_result['results']
        print(f"   Search results found: {len(results)}")
        
        for i, result in enumerate(results[:3]):  # Show first 3 results
            print(f"   Result {i+1}:")
            print(f"     Team: {result['team_id']}")
            for item in result['items'][:2]:  # Show first 2 items per result
                print(f"       - {item['title']}")
                print(f"         URL: {item['source_url']}")
                print(f"         Type: {item['content_type']}")
    else:
        print(f"❌ Knowledge search failed: {search_result.get('error', 'Unknown error')}")
    
    # Example 4: Getting statistics
    print("\n4. Getting Knowledge Statistics")
    print("-" * 40)
    
    stats_result = get_company_knowledge_statistics(
        company_url=company_url,
        team_id=team_id
    )
    
    if stats_result['success']:
        print(f"✅ Statistics retrieved!")
        stats = stats_result['statistics']
        for key, value in stats.items():
            print(f"   {key}: {value}")
    else:
        print(f"❌ Statistics retrieval failed: {stats_result.get('error', 'Unknown error')}")

    '''
def example_url_extraction():
    """Example of URL extraction from text"""
    print("\n" + "="*60)
    print("EXAMPLE: URL EXTRACTION FROM TEXT")
    print("="*60)
    
    # Example text with various URLs
    sample_text = """
    Here's a sample text with various URLs:
    
    Company website: https://interviewing.io
    Blog post: https://blog.example.com/2024/01/important-article
    Documentation: https://docs.example.com/api/v1/reference
    GitHub repository: https://github.com/example/awesome-project
    Medium article: https://medium.com/@author/tech-insights
    Stack Overflow: https://stackoverflow.com/questions/12345/example-question
    
    Some invalid URLs that should be ignored:
    - not-a-url
    - ftp://old-protocol.com (not http/https)
    - just text without protocol
    """
    
    print("Sample text:")
    print(sample_text)
    
    # Extract URLs
    urls = extract_urls_from_text(sample_text)
    
    print(f"\nExtracted URLs ({len(urls)} found):")
    for i, url in enumerate(sorted(urls), 1):
        print(f"  {i}. {url}")


def example_complete_workflow():
    """Example of a complete workflow"""
    print("\n" + "="*60)
    print("EXAMPLE: COMPLETE WORKFLOW")
    print("="*60)
    
    company_url = "https://interviewing.io"
    team_id = "workflow_team_001"
    
    print(f"Starting complete workflow for: {company_url}")
    print(f"Team ID: {team_id}")
    
    # Step 1: Crawl the company
    print("\nStep 1: Crawling company website...")
    crawl_result = crawl_company(
        company_url=company_url,
        max_pages=5,
        skip_external=True,
        skip_founder_blogs=True,
        skip_founder_search=True,
        simple_output=True
    )
    
    if not crawl_result['success']:
        print(f"❌ Workflow failed at crawling step: {crawl_result.get('error', 'Unknown error')}")
        return
    
    print(f"✅ Crawling completed. Found {crawl_result['summary']['total_unique_urls']} URLs")
    
    # Step 2: Add some additional URLs
    print("\nStep 2: Adding additional URLs...")
    add_result = add_urls_to_existing_file(
        company_url=company_url,
        additional_urls=["https://blog.example.com/featured-post"],
        additional_text="Don't miss this: https://medium.com/example/breaking-news"
    )
    
    if add_result['success']:
        print(f"✅ Added {add_result.get('urls_added', 0)} new URLs")
    
    # Step 3: Scrape knowledge
    print("\nStep 3: Scraping knowledge from URLs...")
    scrape_result = scrape_company_knowledge(
        company_url=company_url,
        team_id=team_id,
        processing_mode="multiprocessing",
        save_discovered_urls=True,
        iterative=False
    )
    
    if not scrape_result['success']:
        print(f"❌ Workflow failed at scraping step: {scrape_result.get('error', 'Unknown error')}")
        return
    
    stats = scrape_result['statistics']
    print(f"✅ Knowledge scraping completed!")
    print(f"   URLs processed: {stats.get('urls_processed', 0)}")
    print(f"   Knowledge items saved: {stats.get('knowledge_items_saved', 0)}")
    
    # Step 4: Search the knowledge
    print("\nStep 4: Searching knowledge...")
    search_result = search_company_knowledge(
        company_url=company_url,
        team_id=team_id,
        query="example"
    )
    
    if search_result['success']:
        results = search_result['results']
        print(f"✅ Search completed! Found {len(results)} result sets")
    
    # Step 5: Get final statistics
    print("\nStep 5: Getting final statistics...")
    stats_result = get_company_knowledge_statistics(
        company_url=company_url,
        team_id=team_id
    )
    
    if stats_result['success']:
        stats = stats_result['statistics']
        print(f"✅ Final statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    
    print(f"\n🎉 Complete workflow finished successfully!")


def main():
    """Run all examples"""
    print("COMPANY CRAWLER & SCRAPPER API EXAMPLES")
    print("="*80)
    
    # Run examples
    # example_url_extraction()
    # example_crawler_usage()
    # example_scrapper_usage()
    example_complete_workflow()
    
    print("\n" + "="*80)
    print("EXAMPLES COMPLETED")
    print("="*80)
    print("These examples demonstrate how to use the new function-based APIs")
    print("for both the Crawler and Scrapper components.")
    print("\nKey features demonstrated:")
    print("- URL extraction from text")
    print("- Company crawling with additional URLs")
    print("- Adding URLs to existing files")
    print("- Knowledge scraping and searching")
    print("- Complete workflow integration")


if __name__ == "__main__":
    main()
