#!/usr/bin/env python3
"""
Test script to async process specific URLs.
"""

import os
import sys
import logging
import asyncio
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import KnowledgeScraper, setup_logging

async def test_async_url_processing():
    """Test async processing of specific URLs."""
    print("🧪 Testing Async URL Processing")
    print("=" * 60)
    
    # Create a test URL file with the specific URLs
    test_file = "test_specific_urls.txt"
    test_urls = [
        "https://drive.google.com/file/d/10W-Wl8DMISmLe6z1GnTu09sEyuX9dnm6/view",
        "https://interviewing.io/blog"
    ]
    
    # Write test URLs to file
    with open(test_file, 'w') as f:
        for url in test_urls:
            f.write(f"{url}\n")
    
    print(f"📝 Created test file: {test_file}")
    print(f"🔗 Test URLs:")
    for i, url in enumerate(test_urls, 1):
        print(f"   {i}. {url}")
    print()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        start_time = time.time()
        
        # Initialize scraper with async mode
        async with KnowledgeScraper("test_team_123", "test_user", "async") as scraper:
            print("✅ Async components initialized")
            print(f"   - URL Processor: {'✅' if scraper.url_processor else '❌'}")
            print(f"   - Content Extractor: {'✅' if scraper.content_extractor else '❌'}")
            print(f"   - LLM Processor: {'✅' if scraper.llm_processor else '❌'}")
            print(f"   - Database Handler: {'✅' if scraper.db_handler else '❌'}")
            print()
            
            # Test basic async processing
            print("🚀 Starting async processing...")
            stats = await scraper._process_url_file_async(test_file, save_discovered_urls=True)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"\n✅ Processing completed in {processing_time:.2f} seconds")
            print("\n📊 Processing Results:")
            print("-" * 40)
            for key, value in stats.items():
                if key != 'errors':
                    print(f"  {key}: {value}")
            
            if stats['errors']:
                print("\n❌ Errors:")
                for error in stats['errors']:
                    print(f"  - {error}")
            
            # Check if URLs were discovered and saved
            if stats.get('subpages_discovered', 0) > 0:
                print(f"\n🔍 Subpage Discovery:")
                print(f"   - Discovered {stats['subpages_discovered']} subpages")
                print(f"   - Check the updated {test_file} for all discovered URLs")
            
            # Check if content was extracted
            if stats.get('content_extracted', 0) > 0:
                print(f"\n📄 Content Extraction:")
                print(f"   - Extracted content from {stats['content_extracted']} URLs")
            
            # Check if knowledge was saved
            if stats.get('knowledge_items_saved', 0) > 0:
                print(f"\n💾 Knowledge Storage:")
                print(f"   - Saved {stats['knowledge_items_saved']} knowledge items to database")
            
            return True, processing_time, stats
            
    except Exception as e:
        logger.error(f"Async processing test failed: {e}")
        print(f"❌ Async processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, 0, {}
    
    finally:
        # Cleanup test files
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n🧹 Cleaned up: {test_file}")

async def test_individual_url_processing():
    """Test processing individual URLs to see detailed results."""
    print("\n🧪 Testing Individual URL Processing")
    print("=" * 60)
    
    test_urls = [
        "https://drive.google.com/file/d/10W-Wl8DMISmLe6z1GnTu09sEyuX9dnm6/view",
        "https://interviewing.io/blog"
    ]
    
    async with KnowledgeScraper("test_team_123", "test_user", "async") as scraper:
        for i, url in enumerate(test_urls, 1):
            print(f"\n--- Processing URL {i}: {url} ---")
            
            try:
                # Step 1: Discover subpages
                print("🔍 Discovering subpages...")
                if scraper.url_processor:
                    subpages = await scraper.url_processor.discover_subpages(url)
                    print(f"   Found {len(subpages)} subpages")
                    if subpages:
                        print(f"   Sample subpages:")
                        for j, subpage in enumerate(subpages[:3], 1):
                            print(f"     {j}. {subpage}")
                        if len(subpages) > 3:
                            print(f"     ... and {len(subpages) - 3} more")
                else:
                    print("   ❌ URL processor not available")
                    continue
                
                # Step 2: Extract content
                print("📄 Extracting content...")
                if scraper.content_extractor:
                    content_data = await scraper.content_extractor.extract_content(url)
                    if content_data:
                        print(f"   ✅ Content extracted successfully")
                        print(f"   Title: {content_data.get('title', 'No title')}")
                        print(f"   Content Type: {content_data.get('content_type', 'Unknown')}")
                        print(f"   Author: {content_data.get('author', 'No author')}")
                        print(f"   Content Length: {len(content_data.get('content', ''))} characters")
                        
                        # Step 3: Validate content
                        print("🤖 Validating content...")
                        if scraper.llm_processor:
                            is_valid = await scraper.llm_processor.validate_content(content_data)
                            print(f"   Content valid: {is_valid}")
                            
                            if is_valid:
                                # Step 4: Process with LLM
                                print("🧠 Processing with LLM...")
                                knowledge_data = await scraper.llm_processor.process_content(
                                    content_data, "test_team_123", "test_user"
                                )
                                if knowledge_data:
                                    print(f"   ✅ Knowledge extracted successfully")
                                    print(f"   Items: {len(knowledge_data.get('items', []))}")
                                    
                                    # Step 5: Save to database
                                    print("💾 Saving to database...")
                                    if scraper.db_handler:
                                        success = await scraper.db_handler.save_knowledge_item(knowledge_data)
                                        print(f"   Save successful: {success}")
                                    else:
                                        print(f"   ❌ Database handler not available")
                                else:
                                    print(f"   ❌ Failed to extract knowledge")
                            else:
                                print(f"   ⚠️  Content not suitable for knowledge extraction")
                        else:
                            print(f"   ❌ LLM processor not available")
                    else:
                        print(f"   ❌ Failed to extract content")
                else:
                    print(f"   ❌ Content extractor not available")
                    
            except Exception as e:
                print(f"   ❌ Error processing {url}: {e}")

def main():
    """Main test function."""
    print("🧪 Async URL Processing Test")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    
    # Run the main async test
    success, processing_time, stats = asyncio.run(test_async_url_processing())
    
    if success:
        print(f"\n🎉 Async processing test completed successfully!")
        print(f"⏱️  Total processing time: {processing_time:.2f} seconds")
        
        # Run individual URL processing for detailed results
        print("\n" + "=" * 60)
        asyncio.run(test_individual_url_processing())
        
        print(f"\n✅ All tests completed!")
        print(f"\nYou can now use async processing with:")
        print(f"python main.py urls.txt --team-id your_team_id --processing-mode async")
    else:
        print(f"\n❌ Async processing test failed!")
        print(f"Please check the error messages above and verify your configuration.")

if __name__ == "__main__":
    main() 