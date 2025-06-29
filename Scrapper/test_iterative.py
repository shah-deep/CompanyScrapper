#!/usr/bin/env python3
"""
Test script for iterative subpage discovery functionality.
This script demonstrates the new iterative scraping capabilities.
"""

import os
import sys
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import KnowledgeScraper, setup_logging

def test_iterative_scraping():
    """Test the iterative scraping functionality."""
    print("🧪 Testing Iterative Subpage Discovery")
    print("=" * 60)
    
    # Create a test URL file
    test_file = "sample_urls.txt"
    test_urls = [
        "https://interviewing.io/blog"
    ]
    
    # Write test URLs to file
    with open(test_file, 'w') as f:
        for url in test_urls:
            f.write(f"{url}\n")
    
    print(f"Created test file: {test_file}")
    print(f"Test URLs: {test_urls}")
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize scraper with test team ID
        with KnowledgeScraper("test_team_123", "test_user") as scraper:
            print("\n🚀 Starting iterative processing...")
            
            # Run iterative processing
            stats = scraper.process_url_file_iterative(test_file)
            
            print("\n📊 Processing Results:")
            print("-" * 40)
            for key, value in stats.items():
                if key != 'errors':
                    print(f"  {key}: {value}")
            
            if stats['errors']:
                print("\n❌ Errors:")
                for error in stats['errors']:
                    print(f"  - {error}")
            
            # Check if subpage file was created
            subpage_file = Path(test_file).parent / f"{Path(test_file).stem}_subpage{Path(test_file).suffix}"
            if subpage_file.exists():
                print(f"\n✅ Subpage file created: {subpage_file}")
                with open(subpage_file, 'r') as f:
                    subpage_urls = f.readlines()
                print(f"   Contains {len(subpage_urls)} discovered URLs")
            else:
                print(f"\n⚠️  Subpage file not found: {subpage_file}")
            
            # Check if original file was updated
            with open(test_file, 'r') as f:
                updated_urls = f.readlines()
            print(f"\n📝 Original file updated: {test_file}")
            print(f"   Now contains {len(updated_urls)} URLs")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")
    
    finally:
        pass
        # Cleanup test files
        # if os.path.exists(test_file):
        #     os.remove(test_file)
        #     print(f"\n🧹 Cleaned up: {test_file}")
        
        # subpage_file = Path(test_file).parent / f"{Path(test_file).stem}_subpage{Path(test_file).suffix}"
        # if subpage_file.exists():
        #     subpage_file.unlink()
        #     print(f"🧹 Cleaned up: {subpage_file}")

def main():
    """Main test function."""
    print("🧪 Knowledge Scraper - Iterative Test")
    print("=" * 60)
    
    test_iterative_scraping()
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main() 