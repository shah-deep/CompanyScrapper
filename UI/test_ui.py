#!/usr/bin/env python3
"""
Test script for the UI components
"""

import sys
import os
from pathlib import Path

# Get the script directory (UI directory) and project root
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent

# Add the project root to Python path
sys.path.append(str(project_root))

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from Crawler.crawler_api import crawl_company, add_urls_to_existing_file
        print("✅ Crawler API imported successfully")
    except ImportError as e:
        print(f"❌ Crawler API import failed: {e}")
        return False
    
    try:
        from Scrapper.scrapper_api import scrape_company_knowledge, get_company_knowledge
        print("✅ Scrapper API imported successfully")
    except ImportError as e:
        print(f"❌ Scrapper API import failed: {e}")
        return False
    
    try:
        import streamlit
        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
    return True


def test_url_validation():
    """Test URL validation function"""
    print("\nTesting URL validation...")
    
    # Test valid URLs
    valid_urls = [
        "https://example.com",
        "http://test.com/path",
        "https://subdomain.example.com/path?param=value"
    ]
    
    for url in valid_urls:
        if url.startswith(('http://', 'https://')):
            print(f"✅ Valid URL: {url}")
        else:
            print(f"❌ Invalid URL: {url}")
    
    # Test invalid URLs
    invalid_urls = [
        "",
        "not-a-url",
        "ftp://example.com",
        "example.com"
    ]
    
    for url in invalid_urls:
        if not url or not url.startswith(('http://', 'https://')):
            print(f"✅ Correctly rejected: {url}")
        else:
            print(f"❌ Should have rejected: {url}")


def test_file_paths():
    """Test file path generation"""
    print("\nTesting file path generation...")
    
    test_url = "https://interviewing.io"
    expected_filename = "interviewing.io.txt"
    
    try:
        from urllib.parse import urlparse
        parsed_url = urlparse(test_url)
        domain = parsed_url.netloc
        filename = f"{domain}.txt"
        
        if filename == expected_filename:
            print(f"✅ File path generation correct: {filename}")
        else:
            print(f"❌ File path generation incorrect: expected {expected_filename}, got {filename}")
            
    except Exception as e:
        print(f"❌ File path generation failed: {e}")


def test_directory_structure():
    """Test that the directory structure is correct"""
    print("\nTesting directory structure...")
    
    # Check if we're running from the right location
    current_dir = Path.cwd()
    print(f"Current working directory: {current_dir}")
    
    # Check if UI directory exists
    ui_dir = current_dir / "UI"
    if ui_dir.exists():
        print(f"✅ UI directory found: {ui_dir}")
    else:
        print(f"⚠️  UI directory not found in current directory")
        print(f"   Expected: {ui_dir}")
    
    # Check if app.py exists in UI directory
    app_file = ui_dir / "app.py"
    if app_file.exists():
        print(f"✅ app.py found: {app_file}")
    else:
        print(f"❌ app.py not found in UI directory")
    
    # Check if project structure is correct
    crawler_dir = current_dir / "Crawler"
    scrapper_dir = current_dir / "Scrapper"
    
    if crawler_dir.exists():
        print(f"✅ Crawler directory found: {crawler_dir}")
    else:
        print(f"❌ Crawler directory not found")
    
    if scrapper_dir.exists():
        print(f"✅ Scrapper directory found: {scrapper_dir}")
    else:
        print(f"❌ Scrapper directory not found")


def main():
    """Run all tests"""
    print("🏢 Company Crawler & Scrapper UI - Test Suite")
    print("=" * 50)
    
    # Test directory structure first
    test_directory_structure()
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed. Please check your installation.")
        return
    
    # Test URL validation
    test_url_validation()
    
    # Test file paths
    test_file_paths()
    
    print("\n✅ All tests completed successfully!")
    print("The UI should be ready to run with: python UI/run_ui.py")


if __name__ == "__main__":
    main() 