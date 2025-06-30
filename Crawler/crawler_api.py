#!/usr/bin/env python3
"""
Company Crawler API - Function-based interface for the crawler component
"""

import re
import os
from urllib.parse import urlparse
from typing import List, Set, Dict, Any, Optional

from .company_extractor import CompanyExtractor
from .web_crawler import WebCrawler, crawl_trusted_base_urls
from .blog_discovery import BlogDiscovery
from .founder_discovery import FounderDiscovery
from .url_aggregator import URLAggregator
from .config import GOOGLE_API_KEY, GEMINI_API_KEY, SKIP_URL_WORDS


def extract_urls_from_text(text: str) -> Set[str]:
    """
    Extract URLs from text content (paragraph, string, etc.)
    
    Args:
        text: Text content that may contain URLs
        
    Returns:
        Set of unique URLs found in the text
    """
    # URL regex pattern - matches http/https URLs
    url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
    
    # Find all URLs in the text
    urls = re.findall(url_pattern, text)
    
    # Clean and validate URLs
    valid_urls = set()
    for url in urls:
        # Remove trailing punctuation that might be part of the text
        url = url.rstrip('.,;:!?')
        
        # Validate URL
        try:
            result = urlparse(url)
            if all([result.scheme, result.netloc]):
                valid_urls.add(url)
        except:
            continue
    
    return valid_urls


def get_skip_words(user_skip_words: Optional[List[str]] = None) -> List[str]:
    """Merge default skip words with user-provided ones"""
    all_skip_words = list(SKIP_URL_WORDS)  # Copy default list
    if user_skip_words:
        for word in user_skip_words:
            if word.lower() not in [w.lower() for w in all_skip_words]:
                all_skip_words.append(word.lower())
    return all_skip_words


def validate_url(url: str) -> bool:
    """Validate if the provided URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def crawl_company(
    company_url: str,
    team_id: str,
    additional_urls: Optional[List[str]] = None,
    additional_text: Optional[str] = None,
    max_pages: int = 50,
    skip_external: bool = False,
    skip_founder_blogs: bool = False,
    skip_founder_search: bool = False,
    skip_words: Optional[List[str]] = None,
    output_file: Optional[str] = None,
    simple_output: bool = True
) -> Dict[str, Any]:
    """
    Crawl a company website and discover related URLs
    
    Args:
        company_url: The company homepage URL to analyze
        team_id: Team ID for organizing the data
        additional_urls: List of additional URLs to include
        additional_text: Text content that may contain URLs to extract
        max_pages: Maximum pages to crawl on company website
        skip_external: Skip external mentions search
        skip_founder_blogs: Skip founder blog search
        skip_founder_search: Skip founder discovery search
        skip_words: Additional words to skip in URLs
        output_file: Custom output filename
        simple_output: Generate simple URL list (True) or comprehensive report (False)
        
    Returns:
        Dictionary containing results and file paths
    """
    # Validate company URL
    if not validate_url(company_url):
        raise ValueError(f"Invalid company URL: {company_url}")
    
    # Check API availability
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not found. Company info extraction will use basic methods.")
    
    if not GOOGLE_API_KEY and (not skip_external or not skip_founder_blogs or not skip_founder_search):
        print("Warning: GOOGLE_API_KEY not found. External search features will be disabled.")
        skip_external = True
        skip_founder_blogs = True
        skip_founder_search = True
    
    # Get merged skip words
    all_skip_words = get_skip_words(skip_words)
    
    # Initialize components
    extractor = CompanyExtractor()
    crawler = WebCrawler(custom_skip_words=skip_words)
    blog_discovery = BlogDiscovery(custom_skip_words=skip_words)
    founder_discovery = FounderDiscovery(custom_skip_words=skip_words)
    aggregator = URLAggregator()
    
    # Set company URL for filename generation
    aggregator.set_company_url(company_url)
    
    # Extract URLs from additional text if provided
    extracted_urls = set()
    if additional_text:
        extracted_urls = extract_urls_from_text(additional_text)
        print(f"Extracted {len(extracted_urls)} URLs from additional text")
    
    # Combine additional URLs
    all_additional_urls = set()
    if additional_urls:
        for url in additional_urls:
            if validate_url(url):
                all_additional_urls.add(url)
            else:
                print(f"Warning: Invalid URL in additional_urls: {url}")
    
    # Add extracted URLs to additional URLs
    all_additional_urls.update(extracted_urls)
    
    try:
        # Step 1: Extract company information
        print("Extracting company information...")
        company_info = extractor.extract_company_info(company_url)
        
        if not company_info:
            raise RuntimeError("Could not extract company information")
        
        company_name = company_info.get('name', 'Unknown Company')
        founders = company_info.get('founders', [])
        
        print(f"Company: {company_name}")
        print(f"Description: {company_info.get('description', 'N/A')[:100]}...")
        print(f"Industry: {company_info.get('industry', 'N/A')}")
        print(f"Founders: {', '.join(founders) if founders else 'N/A'}")
        
        # Step 1.5: Search for founders if not found
        if not founders and not skip_founder_search:
            print("Searching for founders...")
            
            # Set company info for URL filtering
            founder_discovery.set_company_info(company_name, company_url)
            
            discovered_founders = founder_discovery.search_founders(company_name, company_url)
            if discovered_founders:
                founders = discovered_founders
                company_info['founders'] = founders
                print(f"Updated founders: {', '.join(founders)}")
            else:
                print("No founders found through search")
        
        # Step 2: Crawl company website
        print("Crawling company website...")
        
        # Set company info for URL filtering
        crawler.set_company_info(company_name, company_url)
        
        company_pages, blog_posts = crawler.crawl_company_site(company_url, max_pages)
        
        aggregator.add_company_pages(company_pages)
        aggregator.add_blog_posts(blog_posts)
        
        # Step 3: Search for founder blogs (if enabled and founders found)
        if not skip_founder_blogs and founders:
            print("Searching for founder blogs...")
            
            # Set company info for URL filtering
            blog_discovery.set_company_info(company_name, company_url)
            
            founder_blogs = blog_discovery.search_founder_blogs(company_name, founders)
            aggregator.add_founder_blogs(founder_blogs)
        
        # Step 4: Search for external mentions (if enabled)
        if not skip_external:
            print("Searching for external mentions...")
            
            # Set company info for URL filtering (if not already set)
            if not blog_discovery.company_name:
                blog_discovery.set_company_info(company_name, company_url)
            
            external_mentions, potential_urls = blog_discovery.search_company_mentions(company_name, company_info)
            aggregator.add_external_mentions(external_mentions)
            aggregator.add_potential_urls(potential_urls)
        
        # Step 5: Add additional URLs as external mentions
        if all_additional_urls:
            print(f"Adding {len(all_additional_urls)} additional URLs...")
            additional_mentions = [{'url': url, 'title': f'Additional URL: {url}'} for url in all_additional_urls]
            aggregator.add_external_mentions(additional_mentions)
        
        # Step 6: Generate output files
        print("Generating output files...")
        
        # Print summary
        aggregator.print_summary()
        
        # Generate output files
        output_files = []
        
        if simple_output:
            # Generate simple URL list
            output_file_path = aggregator.generate_simple_url_list(company_name, team_id, output_file)
            output_files.append(output_file_path)
        else:
            # Generate comprehensive URL list
            output_file_path = aggregator.generate_url_list(company_name, output_file)
            output_files.append(output_file_path)
        
        # Prepare return data
        result = {
            'success': True,
            'company_name': company_name,
            'company_info': company_info,
            'output_files': output_files,
            'summary': {
                'company_pages': len(aggregator.all_urls['company_pages']),
                'blog_posts': len(aggregator.all_urls['blog_posts']),
                'founder_blogs': len(aggregator.all_urls['founder_blogs']),
                'external_mentions': len(aggregator.all_urls['external_mentions']),
                'potential_urls': len(aggregator.all_urls['potential_urls']),
                'total_unique_urls': aggregator.get_total_urls(),
                'additional_urls_added': len(all_additional_urls)
            }
        }
        
        print(f"Crawling completed successfully!")
        print(f"Output file: {output_files[0]}")
        
        return result
        
    except Exception as e:
        print(f"Error during crawling: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'output_files': []
        }


def add_urls_to_existing_file(
    team_id: str,
    additional_urls: Optional[List[str]] = None,
    additional_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add URLs to an existing team URL file
    
    Args:
        team_id: The team ID (used to find the existing file)
        additional_urls: List of additional URLs to add
        additional_text: Text content that may contain URLs to extract
        
    Returns:
        Dictionary containing results
    """
    # Extract URLs from additional text if provided
    extracted_urls = set()
    if additional_text:
        extracted_urls = extract_urls_from_text(additional_text)
        print(f"Extracted {len(extracted_urls)} URLs from additional text")
    
    # Combine additional URLs
    all_additional_urls = set()
    if additional_urls:
        for url in additional_urls:
            if validate_url(url):
                all_additional_urls.add(url)
            else:
                print(f"Warning: Invalid URL in additional_urls: {url}")
    
    # Add extracted URLs to additional URLs
    all_additional_urls.update(extracted_urls)
    
    if not all_additional_urls:
        return {
            'success': False,
            'error': 'No valid URLs to add'
        }
    
    # Find the existing file using team_id
    try:
        filename = f"{team_id}.txt"
        
        # Get the output directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        output_dir = os.path.join(project_root, 'data', 'scrapped_urls')
        file_path = os.path.join(output_dir, filename)
        
        if not os.path.exists(file_path):
            return {
                'success': False,
                'error': f'No existing file found for team_id: {team_id}'
            }
        
        # Read existing URLs
        existing_urls = set()
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url:
                    existing_urls.add(url)
        
        # Find new URLs
        new_urls = all_additional_urls - existing_urls
        
        if not new_urls:
            return {
                'success': True,
                'message': 'All URLs already exist in the file',
                'urls_added': 0,
                'file_path': file_path
            }
        
        # Append new URLs to the file
        with open(file_path, 'a', encoding='utf-8') as f:
            for url in sorted(new_urls):
                f.write(f"{url}\n")
        
        return {
            'success': True,
            'message': f'Added {len(new_urls)} new URLs to existing file',
            'urls_added': len(new_urls),
            'file_path': file_path,
            'new_urls': list(new_urls)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }



def crawl_trusted_base_urls_api(
    base_urls: List[str],
    skip_words: Optional[List[str]] = None,
    max_pages_per_domain: int = 50,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    API function to crawl trusted base URLs and save discovered subpages.
    Args:
        base_urls: List of base URLs to crawl.
        skip_words: List of words to skip in URLs.
        max_pages_per_domain: Max pages to crawl per base URL.
        output_file: Output file name (optional).
    Returns:
        dict with keys: success, discovered_urls, output_file
    """
    try:
        discovered_urls = crawl_trusted_base_urls(
            base_urls=base_urls,
            skip_words=skip_words,
            max_pages_per_domain=max_pages_per_domain,
            output_file=output_file
        )
        return {
            'success': True,
            'discovered_urls': list(discovered_urls),
            'output_file': output_file or 'trusted_base_urls.txt'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
