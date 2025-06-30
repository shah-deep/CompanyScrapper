#!/usr/bin/env python3
"""
Company Crawler & Scrapper UI
A Streamlit-based user interface for the Company Crawler and Scrapper system
"""

import streamlit as st
import sys
import os
import json
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Get the script directory (UI directory) and project root
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent
# Add the project root to Python path
sys.path.append(str(project_root))

# Import the API modules
from Crawler.crawler_api import crawl_company, add_urls_to_existing_file, extract_urls_from_text
from Scrapper.scrapper_api import (
    scrape_company_knowledge, 
    search_company_knowledge, 
    get_company_knowledge_statistics,
    get_company_knowledge
)


# Page configuration
st.set_page_config(
    page_title="Company Crawler & Scrapper",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1rem;
        padding: 0.5rem;
        background-color: #f8f9fa;
        border-radius: 5px;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .status-info {
        color: #17a2b8;
        font-weight: bold;
    }
    .progress-container {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def validate_url(url: str) -> bool:
    """Validate if the provided URL is valid"""
    if not url:
        return False
    return url.startswith(('http://', 'https://'))


def get_url_file_path(company_url: str) -> str:
    """Get the URL file path for a given company URL"""
    from urllib.parse import urlparse
    
    try:
        parsed_url = urlparse(company_url)
        domain = parsed_url.netloc
        filename = f"{domain}.txt"
        
        output_dir = project_root / 'data' / 'scrapped_urls'
        file_path = output_dir / filename
        
        return str(file_path)
    except Exception:
        return ""


def read_url_file_content(company_url: str) -> str:
    """Read the content of the URL file for a company"""
    file_path = get_url_file_path(company_url)
    if not file_path or not os.path.exists(file_path):
        return "No URL file found for this company."
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


def crawl_company_worker(company_url: str, additional_urls: list, additional_text: str, 
                        max_pages: int, skip_external: bool, skip_founder_blogs: bool, 
                        skip_founder_search: bool, skip_words: list, progress_placeholder):
    """Worker function for crawling company in a separate thread"""
    try:
        # Update progress
        progress_placeholder.info("Starting company crawling...")
        
        # Perform crawling
        result = crawl_company(
            company_url=company_url,
            additional_urls=additional_urls if additional_urls else None,
            additional_text=additional_text if additional_text else None,
            max_pages=max_pages,
            skip_external=skip_external,
            skip_founder_blogs=skip_founder_blogs,
            skip_founder_search=skip_founder_search,
            skip_words=skip_words if skip_words else None,
            simple_output=True
        )
        
        # Store result in session state
        st.session_state.crawl_result = result
        st.session_state.crawl_completed = True
        
        if result['success']:
            progress_placeholder.success("Crawling completed successfully!")
        else:
            progress_placeholder.error(f"Crawling failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        st.session_state.crawl_result = {'success': False, 'error': str(e)}
        st.session_state.crawl_completed = True
        progress_placeholder.error(f"Crawling failed: {str(e)}")


def scrape_company_worker(company_url: str, team_id: str, user_id: str, 
                         additional_urls: list, additional_text: str,
                         skip_existing_urls: bool, iterative: bool, 
                         processing_mode: str, progress_placeholder):
    """Worker function for scraping company in a separate thread"""
    try:
        # Update progress
        progress_placeholder.info("Starting knowledge scraping...")
        
        # Add additional URLs if provided
        if additional_urls or additional_text:
            add_result = add_urls_to_existing_file(
                company_url=company_url,
                additional_urls=additional_urls if additional_urls else None,
                additional_text=additional_text if additional_text else None
            )
            if add_result['success']:
                progress_placeholder.info(f"Added {add_result.get('urls_added', 0)} new URLs")
        
        # Perform scraping
        result = scrape_company_knowledge(
            company_url=company_url,
            team_id=team_id,
            user_id=user_id,
            processing_mode=processing_mode,
            save_discovered_urls=True,
            iterative=iterative,
            skip_existing_urls=skip_existing_urls
        )
        
        # Store result in session state
        st.session_state.scrape_result = result
        st.session_state.scrape_completed = True
        
        if result['success']:
            progress_placeholder.success("Scraping completed successfully!")
        else:
            progress_placeholder.error(f"Scraping failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        st.session_state.scrape_result = {'success': False, 'error': str(e)}
        st.session_state.scrape_completed = True
        progress_placeholder.error(f"Scraping failed: {str(e)}")


def main():
    """Main application function"""
    
    # Initialize session state
    if 'crawl_completed' not in st.session_state:
        st.session_state.crawl_completed = True
    if 'scrape_completed' not in st.session_state:
        st.session_state.scrape_completed = True
    if 'crawl_result' not in st.session_state:
        st.session_state.crawl_result = None
    if 'scrape_result' not in st.session_state:
        st.session_state.scrape_result = None
    
    # Header
    st.markdown('<h1 class="main-header">🏢 Company Crawler & Scrapper</h1>', unsafe_allow_html=True)
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a section:",
        ["Crawler", "Scrapper", "Check Data"]
    )
    
    # Main content based on selected page
    if page == "Crawler":
        show_crawler_section()
    elif page == "Scrapper":
        show_scrapper_section()
    elif page == "Check Data":
        show_check_data_section()


def show_crawler_section():
    """Display the Crawler section"""
    st.markdown('<h2 class="section-header">🔍 Company Crawler</h2>')
    
    # Input form
    with st.form("crawler_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_url = st.text_input(
                "Company Homepage URL *",
                placeholder="https://example.com",
                help="Enter the main website URL of the company you want to crawl"
            )
            
            max_pages = st.number_input(
                "Maximum Pages to Crawl",
                min_value=1,
                max_value=1000,
                value=20,
                help="Maximum number of pages to crawl on the company website"
            )
            
            skip_external = st.checkbox(
                "Skip External URL Search",
                value=False,
                help="Skip searching for external mentions of the company"
            )
            
            skip_founder_blogs = st.checkbox(
                "Skip Founder Blog Search",
                value=False,
                help="Skip searching for founder blog posts"
            )
            
            skip_founder_search = st.checkbox(
                "Skip Founder Discovery Search",
                value=False,
                help="Skip searching for company founders"
            )
        
        with col2:
            additional_urls = st.text_area(
                "Additional URLs (one per line)",
                placeholder="https://blog.example.com/post1\nhttps://docs.example.com/api",
                help="Enter additional URLs to include in the crawl, one per line"
            )
            
            additional_text = st.text_area(
                "Additional Text with URLs",
                placeholder="Check out this article: https://medium.com/example/post",
                help="Enter text that may contain URLs to extract"
            )
            
            skip_words = st.text_area(
                "Skip Words (one per line)",
                placeholder="login\nsignup\nprivacy",
                help="Enter words to skip in URLs, one per line"
            )
        
        # Convert text inputs to lists
        additional_urls_list = [url.strip() for url in additional_urls.split('\n') if url.strip()] if additional_urls else []
        skip_words_list = [word.strip() for word in skip_words.split('\n') if word.strip()] if skip_words else []
        
        # Submit button
        submit_button = st.form_submit_button(
            "🚀 Start Crawling",
            disabled=not validate_url(company_url) or not st.session_state.crawl_completed
        )
    
    # Handle form submission
    if submit_button and company_url:
        st.session_state.crawl_completed = False
        
        # Create progress placeholder
        progress_placeholder = st.empty()
        
        # Start crawling in a separate thread
        thread = threading.Thread(
            target=crawl_company_worker,
            args=(company_url, additional_urls_list, additional_text, max_pages, 
                  skip_external, skip_founder_blogs, skip_founder_search, 
                  skip_words_list, progress_placeholder)
        )
        thread.start()
        
        # Show progress
        with st.spinner("Crawling in progress..."):
            while not st.session_state.crawl_completed:
                time.sleep(0.1)
                st.rerun()
    # Display results
    if st.session_state.crawl_result:
        st.markdown("### Results")
        
        if st.session_state.crawl_result['success']:
            st.success("✅ Crawling completed successfully!")
            
            # Show summary
            summary = st.session_state.crawl_result.get('summary', {})
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total URLs", summary.get('total_unique_urls', 0))
            with col2:
                st.metric("Company Pages", summary.get('company_pages', 0))
            with col3:
                st.metric("Blog Posts", summary.get('blog_posts', 0))
            
            # Show file content
            st.markdown("### Generated URL File Content")
            file_content = read_url_file_content(company_url)
            st.text_area(
                "URL File Content",
                value=file_content,
                height=300,
                disabled=True
            )
            
        else:
            st.error(f"❌ Crawling failed: {st.session_state.crawl_result.get('error', 'Unknown error')}")


def show_scrapper_section():
    """Display the Scrapper section"""
    st.markdown('<h2 class="section-header">📄 Knowledge Scrapper</h2>', unsafe_allow_html=True)
    
    # Input form
    with st.form("scrapper_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_url = st.text_input(
                "Company Homepage URL *",
                placeholder="https://example.com",
                help="Enter the company URL to scrape knowledge from"
            )
            
            team_id = st.text_input(
                "Team ID *",
                placeholder="team_001",
                help="Enter a unique team identifier"
            )
            
            user_id = st.text_input(
                "User ID (Optional)",
                placeholder="user_001",
                help="Enter an optional user identifier"
            )
            
            processing_mode = st.selectbox(
                "Processing Mode",
                ["multiprocessing", "async"],
                help="Choose the processing mode for scraping"
            )
        
        with col2:
            additional_urls = st.text_area(
                "Additional URLs (one per line)",
                placeholder="https://blog.example.com/post1\nhttps://docs.example.com/api",
                help="Enter additional URLs to add to the existing file"
            )
            
            additional_text = st.text_area(
                "Additional Text with URLs",
                placeholder="Check out this article: https://medium.com/example/post",
                help="Enter text that may contain URLs to extract and add"
            )
            
            skip_existing_urls = st.checkbox(
                "Skip Existing URLs in DB",
                value=True,
                help="Skip URLs that already exist in the database"
            )
            
            iterative = st.checkbox(
                "Iterative Subpage Discovery",
                value=True,
                help="Use iterative subpage discovery for better coverage"
            )
        
        # Convert text inputs to lists
        additional_urls_list = [url.strip() for url in additional_urls.split('\n') if url.strip()] if additional_urls else []
        
        # Submit button
        submit_button = st.form_submit_button(
            "🚀 Start Scraping",
            disabled=not validate_url(company_url) or not team_id or not st.session_state.scrape_completed
        )
    
    # Handle form submission
    if submit_button and company_url and team_id:
        st.session_state.scrape_completed = False
        
        # Create progress placeholder
        progress_placeholder = st.empty()
        
        # Start scraping in a separate thread
        thread = threading.Thread(
            target=scrape_company_worker,
            args=(company_url, team_id, user_id, additional_urls_list, additional_text,
                  skip_existing_urls, iterative, processing_mode, progress_placeholder)
        )
        thread.start()
        
        # Show progress
        with st.spinner("Scraping in progress..."):
            while not st.session_state.scrape_completed:
                time.sleep(0.1)
                st.rerun()
    # Display results
    if st.session_state.scrape_result:
        st.markdown("### Results")
        
        if st.session_state.scrape_result['success']:
            st.success("✅ Scraping completed successfully!")
            
            # Show statistics
            stats = st.session_state.scrape_result.get('statistics', {})
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("URLs Processed", stats.get('urls_processed', 0))
            with col2:
                st.metric("Knowledge Items", stats.get('knowledge_items_saved', 0))
            with col3:
                st.metric("Iterations", stats.get('iterations_completed', 0))
            with col4:
                st.metric("New Links", stats.get('total_new_links_found', 0))
            
        else:
            st.error(f"❌ Scraping failed: {st.session_state.scrape_result.get('error', 'Unknown error')}")


def show_check_data_section():
    """Display the Check Data section"""
    st.markdown('<h2 class="section-header">📊 Check Data</h2>', unsafe_allow_html=True)
    
    # Input form
    with st.form("check_data_form"):
        team_id = st.text_input(
            "Team ID *",
            placeholder="team_001",
            help="Enter the team ID to fetch data for"
        )
        
        company_url = st.text_input(
            "Company URL (Optional)",
            placeholder="https://example.com",
            help="Enter the company URL for context (optional)"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            check_button = st.form_submit_button(
                "📊 Get Statistics",
                disabled=not team_id
            )
        
        with col2:
            fetch_button = st.form_submit_button(
                "📄 Fetch All Data",
                disabled=not team_id
            )
    
    # Handle statistics request
    if check_button and team_id:
        with st.spinner("Fetching statistics..."):
            result = get_company_knowledge_statistics(
                company_url=company_url if company_url else "https://example.com",
                team_id=team_id
            )
        
        if result['success']:
            st.success("✅ Statistics retrieved successfully!")
            
            # Display statistics
            stats = result.get('statistics', {})
            if stats:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Items", stats.get('total_items', 0))
                with col2:
                    st.metric("Unique URLs", stats.get('unique_urls', 0))
                with col3:
                    st.metric("Content Types", stats.get('content_types', 0))
                with col4:
                    st.metric("Last Updated", stats.get('last_updated', 'N/A'))
                
                # Show detailed statistics
                st.markdown("### Detailed Statistics")
                st.json(stats)
            else:
                st.info("No statistics available for this team.")
        else:
            st.error(f"❌ Failed to get statistics: {result.get('error', 'Unknown error')}")
    
    # Handle fetch all data request
    if fetch_button and team_id:
        with st.spinner("Fetching all data..."):
            result = get_company_knowledge(
                company_url=company_url if company_url else "https://example.com",
                team_id=team_id
            )
        
        if result['success']:
            st.success("✅ Data retrieved successfully!")
            
            # Display knowledge data
            knowledge = result.get('knowledge', [])
            if knowledge:
                st.markdown("### All Knowledge Data")
                
                # Show in scrollable JSON format
                st.text_area(
                    "Knowledge Data (JSON)",
                    value=json.dumps(knowledge, indent=2, default=str),
                    height=600,
                    disabled=True
                )
                
                # Show summary
                st.markdown(f"### Summary")
                st.info(f"Retrieved {len(knowledge)} knowledge items for team '{team_id}'")
            else:
                st.info("No knowledge data available for this team.")
        else:
            st.error(f"❌ Failed to fetch data: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main() 