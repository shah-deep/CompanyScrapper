#!/usr/bin/env python3
"""
Company Scrapper API - Function-based interface for the scrapper component
"""

import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import KnowledgeScraper


def get_url_file_path(company_url: str) -> str:
    """
    Get the URL file path for a given company URL
    
    Args:
        company_url: The company URL
        
    Returns:
        Path to the URL file
    """
    from urllib.parse import urlparse
    
    try:
        parsed_url = urlparse(company_url)
        domain = parsed_url.netloc
        filename = f"{domain}.txt"
        
        # Get the project root directory (two levels up from Scrapper)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        output_dir = os.path.join(project_root, 'data', 'scrapped_urls')
        file_path = os.path.join(output_dir, filename)
        
        return file_path
    except Exception as e:
        raise ValueError(f"Invalid company URL: {company_url}")


def scrape_company_knowledge(
    company_url: str,
    team_id: str,
    user_id: str = "",
    processing_mode: str = "multiprocessing",
    save_discovered_urls: bool = True,
    iterative: bool = False,
    skip_existing_urls: bool = False
) -> Dict[str, Any]:
    """
    Scrape knowledge from a company's URL file
    
    Args:
        company_url: The company URL (used to find the URL file)
        team_id: Team ID for organizing knowledge
        user_id: User ID (optional)
        processing_mode: Processing mode ("multiprocessing" or "async")
        save_discovered_urls: Whether to save discovered URLs back to file
        iterative: Whether to use iterative subpage discovery
        skip_existing_urls: Whether to skip URLs that already exist in database
        
    Returns:
        Dictionary containing processing results and statistics
    """
    # Get the URL file path
    url_file_path = get_url_file_path(company_url)
    
    if not os.path.exists(url_file_path):
        return {
            'success': False,
            'error': f'No URL file found for {company_url}. Please run the crawler first.',
            'url_file_path': url_file_path
        }
    
    try:
        # Initialize the scraper
        scraper = KnowledgeScraper(team_id, user_id, processing_mode, skip_existing_urls)
        
        if processing_mode == "async":
            import asyncio
            
            async def run_async():
                async with scraper:
                    if iterative:
                        stats = await scraper._process_url_file_iterative_async(url_file_path)
                    else:
                        stats = await scraper._process_url_file_async(url_file_path, save_discovered_urls)
                    return stats
            
            # Run async function
            stats = asyncio.run(run_async())
        else:
            # Use multiprocessing context manager
            with scraper:
                if iterative:
                    stats = scraper.process_url_file_iterative(url_file_path)
                else:
                    stats = scraper.process_url_file(url_file_path, save_discovered_urls)
        
        # Prepare return data
        result = {
            'success': True,
            'url_file_path': url_file_path,
            'team_id': team_id,
            'user_id': user_id,
            'processing_mode': processing_mode,
            'iterative': iterative,
            'skip_existing_urls': skip_existing_urls,
            'statistics': stats
        }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'url_file_path': url_file_path
        }


def search_company_knowledge(
    company_url: str,
    team_id: str,
    query: str
) -> Dict[str, Any]:
    """
    Search existing knowledge for a company
    
    Args:
        company_url: The company URL (used for context)
        team_id: Team ID for organizing knowledge
        query: Search query
        
    Returns:
        Dictionary containing search results
    """
    try:
        # Initialize the scraper
        scraper = KnowledgeScraper(team_id, "", "multiprocessing")
        
        # Search existing knowledge
        results = scraper.search_knowledge(query)
        
        return {
            'success': True,
            'company_url': company_url,
            'team_id': team_id,
            'query': query,
            'results': results
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'company_url': company_url,
            'team_id': team_id,
            'query': query
        }


def get_company_knowledge_statistics(
    company_url: str,
    team_id: str
) -> Dict[str, Any]:
    """
    Get knowledge statistics for a company
    
    Args:
        company_url: The company URL (used for context)
        team_id: Team ID for organizing knowledge
        
    Returns:
        Dictionary containing knowledge statistics
    """
    try:
        # Initialize the scraper
        scraper = KnowledgeScraper(team_id, "", "multiprocessing")
        
        # Get statistics
        stats = scraper.get_statistics()
        
        return {
            'success': True,
            'company_url': company_url,
            'team_id': team_id,
            'statistics': stats
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'company_url': company_url,
            'team_id': team_id
        }


def get_company_knowledge(
    company_url: str,
    team_id: str
) -> Dict[str, Any]:
    """
    Get all knowledge for a company
    
    Args:
        company_url: The company URL (used for context)
        team_id: Team ID for organizing knowledge
        
    Returns:
        Dictionary containing all knowledge items
    """
    try:
        # Initialize the scraper
        scraper = KnowledgeScraper(team_id, "", "multiprocessing")
        
        # Get team knowledge
        knowledge = scraper.get_team_knowledge()
        
        return {
            'success': True,
            'company_url': company_url,
            'team_id': team_id,
            'knowledge': knowledge
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'company_url': company_url,
            'team_id': team_id
        }
