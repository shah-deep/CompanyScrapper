#!/usr/bin/env python3
"""
Debug test script to diagnose iterative processing issues.
"""

import os
import sys
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import KnowledgeScraper, setup_logging

def debug_iterative_scraping():
    """Debug the iterative scraping functionality."""
    print("🔍 Debug Iterative Subpage Discovery")
    print("=" * 60)
    
    # Create a test URL file
    test_file = "debug_urls.txt"
    test_urls = [
        "https://interviewing.io/mocks/google-system-design-distributed-databases",
        "https://interviewing.io/mocks/google-java-order-statistic-of-an-unsorted-array",
        "https://interviewing.io/mocks/linked-in-java-reverse-word-in-string",
        "https://interviewing.io/mocks/airbnb-python-missing-item-list-difference",
        "https://interviewing.io/mocks/microsoft-go-vertex-distance-order-statistic"
    ]
    
    # Write test URLs to file
    with open(test_file, 'w') as f:
        for url in test_urls:
            f.write(f"{url}\n")
    
    print(f"📝 Created test file: {test_file}")
    print(f"🔗 Test URLs: {test_urls}")
    
    # Setup logging with DEBUG level
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize scraper with test team ID
        with KnowledgeScraper("debug_team_123", "debug_user") as scraper:
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
                if subpage_urls:
                    print("   Sample URLs:")
                    for i, url in enumerate(subpage_urls[:5]):
                        print(f"     {i+1}. {url.strip()}")
            else:
                print(f"\n⚠️  Subpage file not found: {subpage_file}")
            
            # Check if original file was updated
            with open(test_file, 'r') as f:
                updated_urls = f.readlines()
            print(f"\n📝 Original file updated: {test_file}")
            print(f"   Now contains {len(updated_urls)} URLs")
            if len(updated_urls) > len(test_urls):
                print("   New URLs added:")
                for i, url in enumerate(updated_urls[len(test_urls):]):
                    print(f"     {i+1}. {url.strip()}")
            
    except Exception as e:
        logger.error(f"Debug test failed: {e}")
        print(f"❌ Debug test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup test files
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n🧹 Cleaned up: {test_file}")
        
        subpage_file = Path(test_file).parent / f"{Path(test_file).stem}_subpage{Path(test_file).suffix}"
        if subpage_file.exists():
            subpage_file.unlink()
            print(f"🧹 Cleaned up: {subpage_file}")

def main():
    """Main debug function."""
    print("🔍 Knowledge Scraper - Debug Test")
    print("=" * 60)
    
    debug_iterative_scraping()
    
    print("\n✅ Debug test completed!")

if __name__ == "__main__":
    main() 