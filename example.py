#!/usr/bin/env python3
"""
Example usage of the Company Scraper
Demonstrates how to use the components programmatically
"""

from company_extractor import CompanyExtractor
from web_crawler import WebCrawler
from blog_discovery import BlogDiscovery
from founder_discovery import FounderDiscovery
from url_aggregator import URLAggregator
import json

def example_usage():
    """Example of how to use the company scraper components"""
    
    # Example company URL
    company_url = "https://interviewing.io/"
    
    print("Company Scraper - Example Usage")
    print("=" * 50)
    
    # Initialize components
    extractor = CompanyExtractor()
    crawler = WebCrawler()
    blog_discovery = BlogDiscovery()
    founder_discovery = FounderDiscovery()
    aggregator = URLAggregator()
    
    # Set company URL for filename generation
    aggregator.set_company_url(company_url)
    
    try:
        # Step 1: Extract company information
        print(f"\n1. Extracting company info from: {company_url}")
        company_info = extractor.extract_company_info(company_url)
        
        if company_info:
            print(f"Company: {company_info.get('name', 'Unknown')}")
            print(f"Description: {company_info.get('description', 'N/A')[:100]}...")
            print(f"Founders: {company_info.get('founders', [])}")
        else:
            print("Could not extract company information")
            return
        
        # Step 1.5: Search for founders if not found
        # founders = company_info.get('founders', [])
        # if not founders:
        #     print(f"\n1.5. Searching for founders...")
        #     discovered_founders = founder_discovery.search_founders(
        #         company_info.get('name', 'Unknown'), 
        #         company_url
        #     )
        #     if discovered_founders:
        #         founders = discovered_founders
        #         company_info['founders'] = founders
        #         print(f"Found founders: {', '.join(founders)}")
        #     else:
        #         print("No founders found through search")
        
        # # Step 2: Crawl company website
        # print(f"\n2. Crawling company website")
        # company_pages, blog_posts = crawler.crawl_company_site(company_url, max_pages=10)
        
        # print(f"Found {len(company_pages)} company pages")
        # print(f"Found {len(blog_posts)} blog posts")
        
        # # Add to aggregator
        # aggregator.add_company_pages(company_pages)
        # aggregator.add_blog_posts(blog_posts)
        
        # # Step 3: Search for founder blogs (if founders found)
        # if founders:
        #     print(f"\n3. Searching for founder blogs")
        #     founder_blogs = blog_discovery.search_founder_blogs(
        #         company_info.get('name', 'Unknown'), 
        #         founders
        #     )
        #     aggregator.add_founder_blogs(founder_blogs)
        #     print(f"Found {len(founder_blogs)} founder blogs")
        # else:
        #     print(f"\n3. No founders found, skipping founder blog search")
        
        # Step 4: Search for external mentions
        print(f"\n4. Searching for external mentions")
        external_mentions = blog_discovery.search_company_mentions(
            company_info.get('name', 'Unknown')
        )
        aggregator.add_external_mentions(external_mentions)
        print(f"Found {len(external_mentions)} external mentions")
        
        # Step 5: Generate reports
        print(f"\n5. Generating reports")
        aggregator.print_summary()
        
        # Generate output files
        company_name = company_info.get('name', 'Unknown_Company')
        url_file = aggregator.generate_url_list(company_name)
        simple_file = aggregator.generate_simple_url_list(company_name)
        json_file = aggregator.generate_json_report(company_name)
        
        print(f"\nGenerated files:")
        print(f"  - {url_file}")
        print(f"  - {simple_file}")
        print(f"  - {json_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    example_usage() 