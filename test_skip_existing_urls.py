#!/usr/bin/env python3
"""
Test script to demonstrate the skip_existing_urls feature
"""

import os
import sys
from pathlib import Path

# Add the Scrapper directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
scrapper_dir = os.path.join(current_dir, 'Scrapper')
sys.path.append(scrapper_dir)

from Scrapper.scrapper_api import scrape_company_knowledge

def test_skip_existing_urls():
    """Test the skip_existing_urls feature."""
    
    # Test parameters
    company_url = "https://example.com"  # This will look for example.com.txt in data/scrapped_urls/
    team_id = "test_team_123"
    user_id = "test_user"
    
    print("Testing skip_existing_urls feature...")
    print(f"Company URL: {company_url}")
    print(f"Team ID: {team_id}")
    print(f"User ID: {user_id}")
    print("-" * 50)
    
    # First run: Process all URLs normally
    print("\n1. First run - Processing all URLs:")
    result1 = scrape_company_knowledge(
        company_url=company_url,
        team_id=team_id,
        user_id=user_id,
        processing_mode="multiprocessing",
        save_discovered_urls=True,
        iterative=False,
        skip_existing_urls=False  # Process all URLs
    )
    
    if result1['success']:
        stats1 = result1['statistics']
        print(f"   URLs processed: {stats1.get('urls_processed', 0)}")
        print(f"   URLs failed: {stats1.get('urls_failed', 0)}")
        print(f"   URLs skipped: {stats1.get('urls_skipped', 0)}")
        print(f"   Content extracted: {stats1.get('content_extracted', 0)}")
        print(f"   Knowledge items saved: {stats1.get('knowledge_items_saved', 0)}")
    else:
        print(f"   Error: {result1['error']}")
    
    # Second run: Skip existing URLs
    print("\n2. Second run - Skipping existing URLs:")
    result2 = scrape_company_knowledge(
        company_url=company_url,
        team_id=team_id,
        user_id=user_id,
        processing_mode="multiprocessing",
        save_discovered_urls=True,
        iterative=False,
        skip_existing_urls=True  # Skip URLs already in database
    )
    
    if result2['success']:
        stats2 = result2['statistics']
        print(f"   URLs processed: {stats2.get('urls_processed', 0)}")
        print(f"   URLs failed: {stats2.get('urls_failed', 0)}")
        print(f"   URLs skipped: {stats2.get('urls_skipped', 0)}")
        print(f"   Content extracted: {stats2.get('content_extracted', 0)}")
        print(f"   Knowledge items saved: {stats2.get('knowledge_items_saved', 0)}")
    else:
        print(f"   Error: {result2['error']}")
    
    print("\n" + "=" * 50)
    print("Test completed!")
    
    # Summary
    if result1['success'] and result2['success']:
        skipped_count = stats2.get('urls_skipped', 0)
        if skipped_count > 0:
            print(f"\n✅ SUCCESS: {skipped_count} URLs were skipped in the second run!")
            print("This confirms that the skip_existing_urls feature is working correctly.")
        else:
            print("\n⚠️  NOTE: No URLs were skipped. This could mean:")
            print("   - No URLs were found in the URL file")
            print("   - No URLs were successfully processed in the first run")
            print("   - The database connection failed")

if __name__ == "__main__":
    test_skip_existing_urls() 