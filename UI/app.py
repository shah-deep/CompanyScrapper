#!/usr/bin/env python3
"""
Company Crawler & Scrapper UI - Flask Version
A modern, elegant web interface for the Company Crawler and Scrapper system
"""

from importlib import reload
import os
import sys
import json
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import queue

# Get the script directory (UI directory) and project root
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent
# Add the project root to Python path
sys.path.append(str(project_root))

# Import the API modules
from Crawler.crawler_api import crawl_company, add_urls_to_existing_file, extract_urls_from_text, crawl_trusted_base_urls_api
from Scrapper.scrapper_api import (
    scrape_company_knowledge, 
    search_company_knowledge, 
    get_company_knowledge_statistics,
    get_company_knowledge
)

app = Flask(__name__)
app.secret_key = 'company_scrapper_secret_key_2024'

# Global state for background tasks
task_queue = queue.Queue()
active_tasks = {}

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


def extract_urls_from_combined_input(text: str) -> tuple[list, str]:
    """Extract URLs from combined input"""
    if not text:
        return [], ""
    
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    urls = []
    remaining_text_parts = []
    
    for line in lines:
        if ',' in line:
            parts = [part.strip() for part in line.split(',')]
            for part in parts:
                if validate_url(part):
                    urls.append(part)
                else:
                    remaining_text_parts.append(part)
        elif validate_url(line):
            urls.append(line)
        else:
            remaining_text_parts.append(line)
    
    if remaining_text_parts:
        remaining_text = '\n'.join(remaining_text_parts)
        extracted_urls = extract_urls_from_text(remaining_text)
        urls.extend(extracted_urls)
    else:
        remaining_text = ""
    
    return urls, remaining_text


def deduplicate_url_file(team_id: str, company_url: str = ""):
    """Deduplicate the URL file for a team and normalize the company_url (no trailing slash)."""
    if team_id is None:
        return
    file_path = get_url_file_path(team_id)
    if not file_path or not os.path.exists(file_path):
        return
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        # Normalize company_url (remove trailing slash)
        normalized_company_url = None
        if company_url:
            normalized_company_url = company_url.rstrip('/')
        deduped = set()
        result = []
        for url in urls:
            # If this is the company_url with trailing slash, skip it if the version without slash exists
            if normalized_company_url and (url == normalized_company_url + '/'): 
                if normalized_company_url in deduped:
                    continue  # skip the version with slash if the one without exists
            # Always store the normalized version only once
            if normalized_company_url and url.rstrip('/') == normalized_company_url:
                if normalized_company_url not in deduped:
                    result.append(normalized_company_url)
                    deduped.add(normalized_company_url)
                continue
            if url not in deduped:
                result.append(url)
                deduped.add(url)
        with open(file_path, 'w', encoding='utf-8') as f:
            for url in result:
                f.write(url + '\n')
    except Exception as e:
        print(f"Error during deduplication: {e}")


def crawl_company_worker(task_id: str, company_url: str, team_id: str, additional_urls: list, 
                        additional_text: str, max_pages: int, skip_external: bool, 
                        skip_founder_blogs: bool, skip_founder_search: bool, skip_words: list):
    """Worker function for crawling company in a separate thread"""
    
    team_id = team_id.lower()
    active_tasks[task_id] = {
        'status': 'running',
        'progress': 'Starting company crawling...',
        'result': None
    }


    def add_discovered_subpages_when_file_exists():
        file_path = get_url_file_path(team_id)
        # Ensure the file exists, create if not
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    pass
                active_tasks[task_id]['progress'] += " URL file did not exist, created new file."
            except Exception as e:
                active_tasks[task_id]['progress'] += f" Failed to create URL file: {str(e)}"
                return
        # Wait for the file to exist (max 60s)
        for _ in range(60):
            if os.path.exists(file_path):
                break
            time.sleep(1)
        else:
            active_tasks[task_id]['progress'] += f" Timed out waiting for URL file to be created."
            return
        # Always add the original additional_urls themselves first
        if additional_urls:
            add_result = add_urls_to_existing_file(
                team_id=team_id,
                additional_urls=additional_urls
            )
            if add_result.get('success'):
                active_tasks[task_id]['progress'] += f" Added {add_result.get('urls_added', 0)} original additional URLs."
            else:
                active_tasks[task_id]['progress'] += f" Failed to add original additional URLs: {add_result.get('error', 'Unknown error')}"
        
        # Ensure at least the company_url is used for blog subpage search
        base_urls_for_crawl = additional_urls if additional_urls else [company_url]
        crawl_result = crawl_trusted_base_urls_api(
            base_urls=base_urls_for_crawl,
            skip_words=skip_words if skip_words else None,
            max_pages_per_domain=max_pages,
            output_file=file_path,
            homepage_url=company_url
        )
        if crawl_result.get('success'):
            discovered_urls = crawl_result.get('discovered_urls', [])
            add_result = add_urls_to_existing_file(
                team_id=team_id,
                additional_urls=discovered_urls
            )
            if add_result.get('success'):
                active_tasks[task_id]['progress'] += f" Added {add_result.get('urls_added', 0)} discovered subpages from additional URLs."
            else:
                active_tasks[task_id]['progress'] += f" Failed to add discovered subpages: {add_result.get('error', 'Unknown error')}"
        else:
            active_tasks[task_id]['progress'] += f" Failed to crawl additional URLs: {crawl_result.get('error', 'Unknown error')}"
        # Also add any additional_text URLs
        if additional_text:
            add_result = add_urls_to_existing_file(
                team_id=team_id,
                additional_text=additional_text
            )
            if add_result.get('success'):
                active_tasks[task_id]['progress'] += f" Added {add_result.get('urls_added', 0)} URLs from additional text."
            else:
                active_tasks[task_id]['progress'] += f" Failed to add URLs from additional text: {add_result.get('error', 'Unknown error')}"

    # Start the background thread for subpage discovery and URL addition
    threading.Thread(target=add_discovered_subpages_when_file_exists, daemon=True).start()

    try:
        # Perform crawling (this will create the file)
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

        # Deduplicate the file after all crawling is complete
        deduplicate_url_file(team_id, company_url)

        active_tasks[task_id] = {
            'status': 'completed',
            'progress': 'Crawling completed successfully!' if result['success'] else f'Crawling failed: {result.get("error", "Unknown error")}',
            'result': result
        }
            
    except Exception as e:
        active_tasks[task_id] = {
            'status': 'failed',
            'progress': f'Crawling failed: {str(e)}',
            'result': {'success': False, 'error': str(e)}
        }


def scrape_company_worker(task_id: str, team_id: str, user_id: str, additional_urls: list, 
                         additional_text: str, skip_existing_urls: bool, iterative: bool, 
                         processing_mode: str):
    """Worker function for scraping company in a separate thread"""
    try:
        team_id = team_id.lower()
        active_tasks[task_id] = {
            'status': 'running',
            'progress': 'Starting knowledge scraping...',
            'result': None
        }
        
        # Ensure the file exists if additional URLs or text are provided
        file_path = get_url_file_path(team_id)
        if (additional_urls or additional_text) and not os.path.exists(file_path):
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    pass
                active_tasks[task_id]['progress'] += " URL file did not exist, created new file."
            except Exception as e:
                active_tasks[task_id]['progress'] += f" Failed to create URL file: {str(e)}"
                return
        
        # Perform scraping
        active_tasks[task_id]['progress'] = 'Processing URLs and extracting knowledge...'
        result = scrape_company_knowledge(
            team_id=team_id,
            user_id=user_id,
            processing_mode=processing_mode,
            save_discovered_urls=True,
            iterative=iterative,
            skip_existing_urls=skip_existing_urls
        )
        
        active_tasks[task_id] = {
            'status': 'completed',
            'progress': 'Scraping completed successfully!' if result['success'] else f'Scraping failed: {result.get("error", "Unknown error")}',
            'result': result
        }
            
    except Exception as e:
        active_tasks[task_id] = {
            'status': 'failed',
            'progress': f'Scraping failed: {str(e)}',
            'result': {'success': False, 'error': str(e)}
        }


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/crawl', methods=['POST'])
def start_crawl():
    """Start crawling process"""
    try:
        data = request.get_json()
        
        # Validate required fields
        company_url = data.get('company_url', '').strip()
        team_id = data.get('team_id', '').strip().lower()
        
        if not validate_url(company_url):
            return jsonify({'success': False, 'error': 'Invalid company URL'}), 400
        
        if not team_id:
            return jsonify({'success': False, 'error': 'Team ID is required'}), 400
        
        # Extract additional data
        additional_input = data.get('additional_input', '')
        skip_words = data.get('skip_words', '')
        max_pages = int(data.get('max_pages', 20))
        skip_external = data.get('skip_external', False)
        # If skipping external, also skip founder blogs
        skip_founder_blogs = skip_external
        
        # Process inputs
        additional_urls_list, additional_text = extract_urls_from_combined_input(additional_input)
        skip_words_list = [word.strip() for word in skip_words.split('\n') if word.strip()] if skip_words else []
        
        # Generate task ID
        task_id = f"crawl_{int(time.time())}_{team_id}"
        
        # Start crawling in background thread
        thread = threading.Thread(
            target=crawl_company_worker,
            args=(task_id, company_url, team_id, additional_urls_list, additional_text, 
                  max_pages, skip_external, skip_founder_blogs, False, skip_words_list)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Crawling started successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scrape', methods=['POST'])
def start_scrape():
    """Start scraping process"""
    try:
        data = request.get_json()
        
        # Validate required fields
        team_id = data.get('team_id', '').strip().lower()
        
        if not team_id:
            return jsonify({'success': False, 'error': 'Team ID is required'}), 400
        
        # Extract additional data
        user_id = data.get('user_id', '').strip()
        additional_input = data.get('additional_input', '')
        skip_existing_urls = data.get('skip_existing_urls', True)
        iterative = data.get('iterative', True)
        processing_mode = data.get('processing_mode', 'multiprocessing')
        
        # Process inputs
        additional_urls_list, additional_text = extract_urls_from_combined_input(additional_input)
        
        # Generate task ID
        task_id = f"scrape_{int(time.time())}_{team_id}"
        
        # Start scraping in background thread
        thread = threading.Thread(
            target=scrape_company_worker,
            args=(task_id, team_id, user_id, additional_urls_list, additional_text,
                  skip_existing_urls, iterative, processing_mode)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Scraping started successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/task/<task_id>')
def get_task_status(task_id):
    """Get task status"""
    if task_id in active_tasks:
        return jsonify(active_tasks[task_id])
    else:
        return jsonify({'status': 'not_found'}), 404


@app.route('/api/urls/<team_id>')
def get_urls(team_id):
    """Get URL file contents for a team"""
    try:
        team_id = team_id.lower()
        file_content = read_url_file_content(team_id)
        file_path = get_url_file_path(team_id)
        
        if file_content and file_content != "No URL file found for this team.":
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            url_count = len([line for line in file_content.split('\n') if line.strip()])
            
            return jsonify({
                'success': True,
                'content': file_content,
                'file_size': file_size,
                'url_count': url_count,
                'filename': os.path.basename(file_path) if file_path else ''
            })
        else:
            return jsonify({
                'success': False,
                'error': f'No URL file found for team {team_id}'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/data/<team_id>')
def get_data(team_id):
    """Get scraped data for a team"""
    try:
        team_id = team_id.lower()
        result = get_company_knowledge(team_id=team_id)
        
        if result['success']:
            knowledge = result.get('knowledge', [])
            
            # Create minimized version for display
            if knowledge and isinstance(knowledge, dict) and knowledge.get('items'):
                items = knowledge['items']
                minimized_items = []
                
                for item in items:
                    minimized_item = {
                        'title': item.get('title', 'Untitled'),
                        'source_url': item.get('source_url', 'N/A'),
                        'content_type': item.get('content_type', 'N/A'),
                        'created_at': str(item.get('created_at', 'N/A')),
                        'content_preview': item.get('content', '')[:200] + "..." if len(item.get('content', '')) > 200 else item.get('content', ''),
                        'content': item.get('content', 'No content available')
                    }
                    minimized_items.append(minimized_item)
                
                minimized_knowledge = {
                    'team_id': knowledge.get('team_id'),
                    'created_at': str(knowledge.get('created_at', 'N/A')),
                    'updated_at': str(knowledge.get('updated_at', 'N/A')),
                    'total_items': len(items),
                    'items': minimized_items
                }
                
                return jsonify({
                    'success': True,
                    'data': minimized_knowledge
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'No knowledge data found for team {team_id}'
                })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/download/<team_id>')
def download_urls(team_id):
    """Download URL file"""
    try:
        team_id = team_id.lower()
        file_path = get_url_file_path(team_id)
        
        if file_path and os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=f"{team_id}.txt")
        else:
            return jsonify({'success': False, 'error': f'File not found for team {team_id}'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = script_dir / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Create static directory if it doesn't exist
    static_dir = script_dir / 'static'
    static_dir.mkdir(exist_ok=True)
    
    print("🏢 Company Crawler & Scrapper UI - Flask Version")
    print("=" * 50)
    print("Starting server on http://localhost:5000")
    print("Press Ctrl+C to stop")
    
    app.run(debug=False, host='0.0.0.0', port=5000)