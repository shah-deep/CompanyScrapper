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
    page_title="Company Data Crawler & Scrapper",
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


def get_url_file_path(team_id: str) -> str:
    """Get the URL file path for a given team ID"""
    try:
        filename = f"{team_id}.txt"
        
        output_dir = project_root / 'data' / 'scrapped_urls'
        file_path = output_dir / filename
        
        return str(file_path)
    except Exception:
        return ""


def read_url_file_content(team_id: str) -> str:
    """Read the content of the URL file for a team"""
    file_path = get_url_file_path(team_id)
    if not file_path or not os.path.exists(file_path):
        return "No URL file found for this team."
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


def crawl_company_worker(company_url: str, team_id: str, additional_urls: list, additional_text: str, 
                        max_pages: int, skip_external: bool, skip_founder_blogs: bool, 
                        skip_founder_search: bool, skip_words: list, progress_placeholder):
    """Worker function for crawling company in a separate thread"""
    try:
        # Update progress
        progress_placeholder.info("🚀 Starting company crawling...")
        time.sleep(1)
        
        # Perform crawling
        result = crawl_company(
            company_url=company_url,
            team_id=team_id,
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
            progress_placeholder.success("✅ Crawling completed successfully!")
        else:
            progress_placeholder.error(f"❌ Crawling failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        st.session_state.crawl_result = {'success': False, 'error': str(e)}
        st.session_state.crawl_completed = True
        progress_placeholder.error(f"❌ Crawling failed: {str(e)}")


def scrape_company_worker(team_id: str, user_id: str, 
                         additional_urls: list, additional_text: str,
                         skip_existing_urls: bool, iterative: bool, 
                         processing_mode: str, progress_placeholder):
    """Worker function for scraping company in a separate thread"""
    try:
        # Update progress
        progress_placeholder.info("🚀 Starting knowledge scraping...")
        time.sleep(1)
        
        # Add additional URLs if provided
        if additional_urls or additional_text:
            progress_placeholder.info("📝 Adding additional URLs to file...")
            add_result = add_urls_to_existing_file(
                team_id=team_id,
                additional_urls=additional_urls if additional_urls else None,
                additional_text=additional_text if additional_text else None
            )
            if add_result['success']:
                progress_placeholder.info(f"✅ Added {add_result.get('urls_added', 0)} new URLs")
            else:
                progress_placeholder.warning(f"⚠️ Failed to add URLs: {add_result.get('error', 'Unknown error')}")
        
        # Perform scraping
        progress_placeholder.info("🔍 Processing URLs and extracting knowledge...")
        result = scrape_company_knowledge(
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
            progress_placeholder.success("✅ Scraping completed successfully!")
        else:
            progress_placeholder.error(f"❌ Scraping failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        st.session_state.scrape_result = {'success': False, 'error': str(e)}
        st.session_state.scrape_completed = True
        progress_placeholder.error(f"❌ Scraping failed: {str(e)}")


def extract_urls_from_combined_input(text: str) -> tuple[list, str]:
    """
    Extract URLs from combined input that may contain:
    - Line-separated URLs
    - Comma-separated URLs
    - Text with embedded URLs
    
    Returns:
        Tuple of (urls_list, remaining_text)
    """
    if not text:
        return [], ""
    
    # Split by lines first
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    urls = []
    remaining_text_parts = []
    
    for line in lines:
        # Check if line contains only URLs (comma-separated or single)
        if ',' in line:
            # Handle comma-separated URLs
            parts = [part.strip() for part in line.split(',')]
            for part in parts:
                if validate_url(part):
                    urls.append(part)
                else:
                    remaining_text_parts.append(part)
        elif validate_url(line):
            # Single URL on a line
            urls.append(line)
        else:
            # Text content that may contain URLs
            remaining_text_parts.append(line)
    
    # Extract URLs from remaining text using the existing function
    if remaining_text_parts:
        remaining_text = '\n'.join(remaining_text_parts)
        extracted_urls = extract_urls_from_text(remaining_text)
        urls.extend(extracted_urls)
    else:
        remaining_text = ""
    
    return urls, remaining_text


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
    # st.markdown('<h1 class="main-header">🏢 Company Crawler & Scrapper</h1>', unsafe_allow_html=True)
    
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
    st.markdown('<h1 class="main-header">🏢 Crawler</h1>', unsafe_allow_html=True)
    
    # Input form
    with st.form("crawler_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_url = st.text_input(
                "Company Homepage URL *",
                placeholder="https://example.com",
                help="Enter the main website URL of the company you want to crawl"
            )
            
            team_id = st.text_input(
                "Team ID *",
                placeholder="team_001",
                help="Enter a unique team identifier for organizing the data"
            )
            
            skip_words = st.text_area(
                "Skip Words (one per line)",
                placeholder="reddit\nlogin\nterms",
                help="Enter words to skip in URL search, one per line"
            )
            
        
        with col2:
            additional_input = st.text_area(
                "Additional URLs",
                placeholder="URLs starting with https:// or http://",
                help="Enter additional URLs (one per line or comma-separated) and/or any text that may contain some URLs"
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
            
        
        # Convert text inputs to lists
        additional_urls_list, additional_text = extract_urls_from_combined_input(additional_input)
        skip_words_list = [word.strip() for word in skip_words.split('\n') if word.strip()] if skip_words else []
        
        # Show extracted URLs for user feedback
        if additional_urls_list:
            st.info(f"📋 Extracted {len(additional_urls_list)} URLs from input")
            with st.expander("View extracted URLs"):
                for i, url in enumerate(additional_urls_list, 1):
                    st.write(f"{i}. {url}")
                    
        # Submit button
        submit_button = st.form_submit_button(
            "🚀 Start Crawling",
            disabled=((not validate_url(company_url)) or (not team_id) or (not st.session_state.crawl_completed))
        )
    
    # Handle form submission
    if submit_button:
        st.session_state.crawl_completed = False
        print(company_url, team_id)
        
        # Create progress placeholder
        progress_placeholder = st.empty()
        
        # Start crawling in a separate thread
        thread = threading.Thread(
            target=crawl_company_worker,
            args=(company_url, team_id, additional_urls_list, additional_text, max_pages, 
                  skip_external, False, False, 
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
            
            # Add refresh button for file content
            if st.button("🔄 Refresh File Content"):
                st.rerun()
            
            file_content = read_url_file_content(team_id)
            if file_content and file_content != "No URL file found for this team.":
                st.text_area(
                    "URL File Content",
                    value=file_content,
                    height=400,
                    disabled=True,
                    help="Scrollable content of the generated URL file"
                )
                
                # Show file info
                file_path = get_url_file_path(team_id)
                if file_path and os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    url_count = len([line for line in file_content.split('\n') if line.strip()])
                    st.info(f"📄 File: {os.path.basename(file_path)} | Size: {file_size} bytes | URLs: {url_count}")
            else:
                st.warning("No URL file found for this team. Run the crawler first to generate the file.")
            
        else:
            st.error(f"❌ Crawling failed: {st.session_state.crawl_result.get('error', 'Unknown error')}")


def show_scrapper_section():
    """Display the Scrapper section"""
    # st.markdown('<h2 class="section-header">📄 Knowledge Scrapper</h2>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-header">🏢 Scrapper</h1>', unsafe_allow_html=True)
    
    # Show current URL file content if available
    st.markdown("### Current URL File Status")
    team_id_placeholder = st.text_input(
        "Enter team ID to check file status",
        placeholder="team_001",
        help="Enter a team ID to check if a URL file exists and view its content"
    )
    
    if team_id_placeholder:
        file_content = read_url_file_content(team_id_placeholder)
        file_path = get_url_file_path(team_id_placeholder)
        
        if file_content and file_content != "No URL file found for this team.":
            st.success(f"✅ URL file found: {os.path.basename(file_path)}")
            
            # Show file info
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                url_count = len([line for line in file_content.split('\n') if line.strip()])
                st.info(f"📄 File: {os.path.basename(file_path)} | Size: {file_size} bytes | URLs: {url_count}")
            
            # Show file content in expander
            with st.expander("📋 View URL File Content"):
                st.text_area(
                    "URL File Content",
                    value=file_content,
                    height=300,
                    disabled=True,
                    help="Current URLs in the file"
                )
        else:
            st.warning("⚠️ No URL file found for this team. Run the crawler first to generate the file.")
    
    st.markdown("---")

    # Input form
    with st.form("scrapper_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            team_id = st.text_input(
                "Team ID *",
                placeholder="team_001",
                help="Enter the team ID to scrape knowledge from"
            )
            
            user_id = st.text_input(
                "User ID (Optional)",
                placeholder="user_001",
                help="Enter an optional user identifier"
            )
            
            processing_mode = "multiprocessing"
            # processing_mode = st.selectbox(
            #     "Processing Mode",
            #     ["multiprocessing", "async"],
            #     help="Choose the processing mode for scraping"
            # )
        
        with col2:
            additional_input = st.text_area(
                "Additional URLs",
                placeholder="URLs starting with https:// or http://",
                help="Enter additional URLs (one per line or comma-separated) and/or any text that may contain some URLs"
            )
            
            skip_existing_urls = st.checkbox(
                "Skip Existing URLs in DB",
                value=True,
                help="Skip URLs that already exist in the database"
            )
            
            iterative = st.checkbox(
                "Iterative Subpage Discovery",
                value=True,
                help="Iteratively discover URLs from current search for a better coverage"
            )
        
        # Convert text inputs to lists
        additional_urls_list, additional_text = extract_urls_from_combined_input(additional_input)
        
        # Show extracted URLs for user feedback
        if additional_urls_list:
            st.info(f"📋 Extracted {len(additional_urls_list)} URLs from input")
            with st.expander("View extracted URLs"):
                for i, url in enumerate(additional_urls_list, 1):
                    st.write(f"{i}. {url}")
        
        # Submit button
        submit_button = st.form_submit_button(
            "🚀 Start Scraping",
            disabled=not team_id or not st.session_state.scrape_completed
        )
    
    # Handle form submission
    if submit_button and team_id:
        st.session_state.scrape_completed = False
        
        # Create progress placeholder
        progress_placeholder = st.empty()
        
        # Start scraping in a separate thread
        thread = threading.Thread(
            target=scrape_company_worker,
            args=(team_id, user_id, additional_urls_list, additional_text,
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
    # st.markdown('<h2 class="section-header">📊 Check Data</h2>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-header">📊 Check Data</h1>', unsafe_allow_html=True)
    
    # Input form
    with st.form("check_data_form"):
        team_id = st.text_input(
            "Team ID *",
            placeholder="team_001",
            help="Enter the team ID to fetch data for"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            get_urls_button = st.form_submit_button(
                "📄 Get URLs",
                disabled=not team_id,
                help="Get the URL file contents for this team"
            )
        
        with col2:
            fetch_data_button = st.form_submit_button(
                "🗄️ Fetch Scrapped Data",
                disabled=not team_id,
                help="Fetch all scraped knowledge data from database for this team"
            )
    
    # Handle Get URLs request
    if get_urls_button and team_id:
        with st.spinner("📄 Fetching URL file contents..."):
            file_content = read_url_file_content(team_id)
            file_path = get_url_file_path(team_id)
        
        if file_content and file_content != "No URL file found for this team.":
            st.success("✅ URL file retrieved successfully!")
            
            # Show file info
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                url_count = len([line for line in file_content.split('\n') if line.strip()])
                st.info(f"📄 File: {os.path.basename(file_path)} | Size: {file_size} bytes | URLs: {url_count}")
            
            # Show file content in scrollable area
            st.markdown("### URL File Contents")
            st.text_area(
                "URLs (one per line)",
                value=file_content,
                height=400,
                disabled=True,
                help="Scrollable content of the URL file"
            )
        else:
            st.warning(f"📭 No URL file found for team '{team_id}'. Run the crawler first to generate the URL file.")
    
    # Handle Fetch Scrapped Data request
    if fetch_data_button and team_id:
        with st.spinner("🗄️ Fetching scraped data from database..."):
            result = get_company_knowledge(
                team_id=team_id
            )
        
        if result['success']:
            st.success("✅ Data retrieved successfully!")
            
            # Display knowledge data
            knowledge = result.get('knowledge', [])
            if knowledge and isinstance(knowledge, dict) and knowledge.get('items'):
                items = knowledge['items']
                st.markdown("### Scraped Knowledge Data")
                
                # Show summary first
                st.markdown(f"#### Summary")
                st.info(f"📊 Retrieved {len(items)} knowledge items for team '{team_id}'")
                
                # Create minimized version for JSON display
                minimized_items = []
                for item in items:
                    minimized_item = {
                        'title': item.get('title', 'Untitled'),
                        'source_url': item.get('source_url', 'N/A'),
                        'content_type': item.get('content_type', 'N/A'),
                        'created_at': item.get('created_at', 'N/A'),
                        'content_preview': item.get('content', '')[:200] + "..." if len(item.get('content', '')) > 200 else item.get('content', '')
                    }
                    minimized_items.append(minimized_item)
                
                minimized_knowledge = {
                    'team_id': knowledge.get('team_id'),
                    'created_at': knowledge.get('created_at'),
                    'updated_at': knowledge.get('updated_at'),
                    'total_items': len(items),
                    'items': minimized_items
                }
                
                # Show minimized JSON
                st.markdown("#### Data Overview (Minimized JSON)")
                st.text_area(
                    "Knowledge Data (Minimized JSON)",
                    value=json.dumps(minimized_knowledge, indent=2, default=str),
                    height=400,
                    disabled=True,
                    help="Minimized JSON data with content previews (first 200 characters)"
                )
                
                # Show items in expandable format
                st.markdown("#### Detailed Knowledge Items")
                for i, item in enumerate(items, 1):
                    with st.expander(f"Item {i}: {item.get('title', 'Untitled')}"):
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.write("**Source URL:**")
                            st.write(item.get('source_url', 'N/A'))
                            st.write("**Content Type:**")
                            st.write(item.get('content_type', 'N/A'))
                            st.write("**Created At:**")
                            st.write(str(item.get('created_at', 'N/A')))
                        with col2:
                            st.write("**Content:**")
                            content = item.get('content', 'No content available')
                            if len(content) > 500:
                                st.text_area(f"Content (truncated)", value=content[:500] + "...", height=150, disabled=True)
                                if st.button(f"Show full content for item {i}"):
                                    st.text_area(f"Full Content", value=content, height=300, disabled=True)
                            else:
                                st.text_area(f"Content", value=content, height=150, disabled=True)
                
            elif knowledge and isinstance(knowledge, list) and knowledge:
                st.markdown("### Scraped Knowledge Data")
                
                # Show summary
                st.markdown(f"#### Summary")
                st.info(f"📊 Retrieved {len(knowledge)} knowledge items for team '{team_id}'")
                
                # Create minimized version
                minimized_knowledge = []
                for item in knowledge:
                    if isinstance(item, dict):
                        minimized_item = {
                            'title': item.get('title', 'Untitled'),
                            'source_url': item.get('source_url', 'N/A'),
                            'content_type': item.get('content_type', 'N/A'),
                            'content_preview': item.get('content', '')[:200] + "..." if len(item.get('content', '')) > 200 else item.get('content', '')
                        }
                        minimized_knowledge.append(minimized_item)
                    else:
                        minimized_knowledge.append(str(item)[:200] + "..." if len(str(item)) > 200 else str(item))
                
                # Show minimized JSON
                st.text_area(
                    "Knowledge Data (Minimized JSON)",
                    value=json.dumps(minimized_knowledge, indent=2, default=str),
                    height=400,
                    disabled=True,
                    help="Minimized JSON data with content previews"
                )
            else:
                st.info(f"📭 No knowledge data found for team '{team_id}'. Run the scrapper first to generate knowledge data.")
        else:
            st.error(f"❌ Failed to fetch data: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main() 