#!/usr/bin/env python3
"""
Test script to verify subpage file cleanup
"""

import sys
import os

# Add the Scrapper directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'Scrapper'))

from scrapper_api import scrape_company_knowledge

def test_subpage_cleanup():
    """Test that subpage files are deleted after processing"""
    
    print("Testing subpage file cleanup...")
    print("=" * 50)
    
    # Check if subpage file exists before processing
    subpage_file = "data/scrapped_urls/aline123_subpage.txt"
    if os.path.exists(subpage_file):
        print(f"Found existing subpage file: {subpage_file}")
    else:
        print("No existing subpage file found")
    
    # Run the scraper with iterative processing
    result = scrape_company_knowledge(
        team_id="aline123",
        user_id="test_user",
        processing_mode="multiprocessing",
        save_discovered_urls=True,
        iterative=True,
        skip_existing_urls=False
    )
    
    print("\n" + "=" * 50)
    print("Processing completed. Checking for subpage file...")
    
    # Check if subpage file was deleted
    if os.path.exists(subpage_file):
        print(f"ERROR: Subpage file still exists: {subpage_file}")
        print("This means cleanup failed!")
    else:
        print(f"SUCCESS: Subpage file was properly deleted")
    
    print("\nFinal Result:")
    print(f"Success: {result.get('success')}")
    if result.get('error'):
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    test_subpage_cleanup() 