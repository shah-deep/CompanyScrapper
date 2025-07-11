#!/usr/bin/env python3
"""
Company Scraper - Main Application
Scrapes company information and discovers related URLs and blogs
"""

import argparse
import sys
import os
from urllib.parse import urlparse

from .company_extractor import CompanyExtractor
from .web_crawler import WebCrawler
from .blog_discovery import BlogDiscovery
from .founder_discovery import FounderDiscovery
from .url_aggregator import URLAggregator
from .config import GOOGLE_API_KEY, GEMINI_API_KEY, SKIP_URL_WORDS

def validate_url(url):
    """Validate if the provided URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def get_skip_words(user_skip_words):
    """Merge default skip words with user-provided ones"""
    all_skip_words = list(SKIP_URL_WORDS)  # Copy default list
    for word in user_skip_words:
        if word.lower() not in [w.lower() for w in all_skip_words]:
            all_skip_words.append(word.lower())
    return all_skip_words

def main():
    parser = argparse.ArgumentParser(
        description='Company Scraper - Extract company info and discover related URLs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py https://example.com
  python main.py https://startup.com --max-pages 100
  python main.py https://company.com --output my_company_urls.txt
  python main.py https://company.com --skip-words reddit facebook twitter
  python main.py trusted-base-urls --urls https://blog.example.com https://news.example.com --output trusted_urls.txt
        """
    )
    subparsers = parser.add_subparsers(dest='command')

    # Default company crawl parser
    crawl_parser = subparsers.add_parser('crawl', help='Crawl a company website (default)')
    crawl_parser.add_argument('url', help='Company homepage URL to analyze')
    crawl_parser.add_argument('--max-pages', type=int, default=50, help='Maximum pages to crawl on company website (default: 50)')
    crawl_parser.add_argument('--output', help='Output filename for URL list')
    crawl_parser.add_argument('--skip-external', action='store_true', help='Skip external mentions search (requires Google API)')
    crawl_parser.add_argument('--skip-founder-blogs', action='store_true', help='Skip founder blog search (requires Google API)')
    crawl_parser.add_argument('--skip-founder-search', action='store_true', help='Skip founder discovery search (requires Google API)')
    crawl_parser.add_argument('--simple', action='store_true', help='Generate simple URL list only')
    crawl_parser.add_argument('--json', action='store_true', help='Generate JSON report')
    crawl_parser.add_argument('--skip-words', nargs='+', default=[], help='Additional words to skip in URLs (e.g., --skip-words reddit facebook)')

    # Trusted base URLs parser
    trusted_parser = subparsers.add_parser('trusted-base-urls', help='Crawl all subpages for trusted base URLs')
    trusted_parser.add_argument('--urls', nargs='+', required=True, help='List of trusted base URLs to crawl')
    trusted_parser.add_argument('--skip-words', nargs='+', default=[], help='Words to skip in URLs')
    trusted_parser.add_argument('--max-pages', type=int, default=50, help='Maximum pages to crawl per base URL')
    trusted_parser.add_argument('--output', help='Output filename for discovered URLs')

    # If no subcommand, default to crawl
    args = parser.parse_args()
    if args.command is None:
        args = parser.parse_args(['crawl'] + [a for a in vars(args).values() if isinstance(a, str)])

    if args.command == 'trusted-base-urls':
        from .crawler_api import crawl_trusted_base_urls_api
        print("=" * 80)
        print("TRUSTED BASE URL CRAWLER")
        print("=" * 80)
        base_urls_for_crawl = args.urls if args.urls else [args.url]
        print(f"Base URLs: {', '.join(base_urls_for_crawl)}")
        print(f"Max pages per domain: {args.max_pages}")
        if args.skip_words:
            print(f"Skip words: {', '.join(args.skip_words)}")
        print("=" * 80)
        result = crawl_trusted_base_urls_api(
            base_urls=base_urls_for_crawl,
            skip_words=args.skip_words,
            max_pages_per_domain=args.max_pages,
            output_file=args.output,
            homepage_url=args.url
        )
        if result['success']:
            print(f"\nCrawl complete. {len(result['discovered_urls'])} unique URLs saved to {result['output_file']}")
        else:
            print(f"\nError: {result.get('error')}")
        return

    # Validate URL
    if not validate_url(args.url):
        print("Error: Invalid URL provided")
        sys.exit(1)
    
    print("=" * 80)
    print("COMPANY SCRAPER")
    print("=" * 80)
    print(f"Target URL: {args.url}")
    print(f"Max pages to crawl: {args.max_pages}")
    print("=" * 80)
    
    # Check API availability
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not found. Company info extraction will use basic methods.")
    
    if not GOOGLE_API_KEY and (not args.skip_external or not args.skip_founder_blogs or not args.skip_founder_search):
        print("Warning: GOOGLE_API_KEY not found. External search features will be disabled.")
        args.skip_external = True
        args.skip_founder_blogs = True
        args.skip_founder_search = True
    
    # Get merged skip words
    all_skip_words = get_skip_words(args.skip_words)
    if args.skip_words:
        print(f"Using custom skip words: {', '.join(args.skip_words)}")
    
    # Initialize components
    extractor = CompanyExtractor()
    crawler = WebCrawler(custom_skip_words=args.skip_words)
    blog_discovery = BlogDiscovery(custom_skip_words=args.skip_words)
    founder_discovery = FounderDiscovery(custom_skip_words=args.skip_words)
    aggregator = URLAggregator()
    
    # Set company URL for filename generation
    aggregator.set_company_url(args.url)
    
    try:
        # Step 1: Extract company information
        print("\n1. EXTRACTING COMPANY INFORMATION")
        print("-" * 40)
        company_info = extractor.extract_company_info(args.url)
        
        if not company_info:
            print("Error: Could not extract company information")
            sys.exit(1)
        
        company_name = company_info.get('name', 'Unknown Company')
        founders = company_info.get('founders', [])
        
        print(f"Company: {company_name}")
        print(f"Description: {company_info.get('description', 'N/A')[:100]}...")
        print(f"Industry: {company_info.get('industry', 'N/A')}")
        print(f"Founders: {', '.join(founders) if founders else 'N/A'}")
        
        # Step 1.5: Search for founders if not found
        if not founders and not args.skip_founder_search:
            print("\n1.5. SEARCHING FOR FOUNDERS")
            print("-" * 40)
            
            # Set company info for URL filtering
            founder_discovery.set_company_info(company_name, args.url)
            
            discovered_founders = founder_discovery.search_founders(company_name, args.url)
            if discovered_founders:
                founders = discovered_founders
                company_info['founders'] = founders
                print(f"Updated founders: {', '.join(founders)}")
            else:
                print("No founders found through search")
        elif not founders:
            print("\n1.5. SKIPPING FOUNDER SEARCH")
            print("-" * 40)
            print("Skipped by user request or API unavailable")
        else:
            print("\n1.5. SKIPPING FOUNDER SEARCH")
            print("-" * 40)
            print(f"Founders already found during company extraction: {', '.join(founders)}")
        
        # Step 2: Crawl company website
        print("\n2. CRAWLING COMPANY WEBSITE")
        print("-" * 40)
        
        # Set company info for URL filtering
        crawler.set_company_info(company_name, args.url)
        
        company_pages, blog_posts = crawler.crawl_company_site(args.url, args.max_pages)
        
        aggregator.add_company_pages(company_pages)
        aggregator.add_blog_posts(blog_posts)
        
        # Step 3: Search for founder blogs (if enabled and founders found)
        if not args.skip_founder_blogs and founders:
            print("\n3. SEARCHING FOR FOUNDER BLOGS")
            print("-" * 40)
            
            # Set company info for URL filtering
            blog_discovery.set_company_info(company_name, args.url)
            
            founder_blogs = blog_discovery.search_founder_blogs(company_name, founders)
            aggregator.add_founder_blogs(founder_blogs)
        else:
            print("\n3. SKIPPING FOUNDER BLOG SEARCH")
            print("-" * 40)
            if not founders:
                print("No founder information available")
            else:
                print("Skipped by user request or API unavailable")
        
        # Step 4: Search for external mentions (if enabled)
        if not args.skip_external:
            print("\n4. SEARCHING FOR EXTERNAL MENTIONS")
            print("-" * 40)
            
            # Set company info for URL filtering (if not already set)
            if not blog_discovery.company_name:
                blog_discovery.set_company_info(company_name, args.url)
            
            external_mentions, potential_urls = blog_discovery.search_company_mentions(company_name, company_info)
            aggregator.add_external_mentions(external_mentions)
            aggregator.add_potential_urls(potential_urls)
        else:
            print("\n4. SKIPPING EXTERNAL MENTIONS SEARCH")
            print("-" * 40)
            print("Skipped by user request or API unavailable")
        
        # Step 5: Generate reports
        print("\n5. GENERATING REPORTS")
        print("-" * 40)
        
        # Print summary
        aggregator.print_summary()
        
        # Generate output files
        output_files = []
        
        if args.simple:
            # Generate simple URL list
            output_file = aggregator.generate_simple_url_list(company_name, args.output)
            output_files.append(output_file)
        else:
            # Generate comprehensive URL list
            output_file = aggregator.generate_url_list(company_name, args.output)
            output_files.append(output_file)
        
        # Generate JSON report if requested
        if args.json:
            json_file = aggregator.generate_json_report(company_name)
            output_files.append(json_file)
        
        print(f"\nReports generated successfully!")
        for file in output_files:
            print(f"  - {file}")
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 