#!/usr/bin/env python3
"""
Test script specifically for async processing of Google Drive URLs.
"""

import os
import sys
import logging
import asyncio
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_extractor import ContentExtractor
from url_processor import URLProcessor
from llm_processor import LLMProcessor
from database_handler import DatabaseHandler

async def test_google_drive_extraction():
    """Test Google Drive URL extraction specifically."""
    print("🧪 Testing Google Drive URL Extraction")
    print("=" * 60)
    
    # The specific Google Drive URL
    google_drive_url = "https://drive.google.com/file/d/10W-Wl8DMISmLe6z1GnTu09sEyuX9dnm6/view"
    
    print(f"Testing URL: {google_drive_url}")
    print()
    
    try:
        # Initialize components
        async with ContentExtractor() as extractor:
            print("✅ Content extractor initialized")
            
            # Check if it's detected as a Google Drive URL
            is_drive = extractor._is_google_drive_url(google_drive_url)
            print(f"🔍 Detected as Google Drive URL: {is_drive}")
            
            if is_drive:
                # Extract file ID
                file_id = extractor._extract_google_drive_file_id(google_drive_url)
                print(f"📁 Extracted file ID: {file_id}")
                
                # Build download URL
                if file_id:
                    download_url = extractor._build_google_drive_download_url(file_id)
                    print(f"⬇️  Download URL: {download_url}")
                else:
                    print("❌ Could not extract file ID from Google Drive URL")
                print()
            
            # Extract content
            print("🔄 Extracting content...")
            start_time = time.time()
            
            content = await extractor.extract_content(google_drive_url)
            
            end_time = time.time()
            extraction_time = end_time - start_time
            
            if content:
                print(f"✅ Content extracted successfully in {extraction_time:.2f} seconds!")
                print()
                print("📊 Content Summary:")
                print("-" * 40)
                print(f"Title: {content.get('title', 'No title')}")
                print(f"Content Type: {content.get('content_type', 'Unknown')}")
                print(f"Author: {content.get('author', 'No author')}")
                print(f"URL: {content.get('url', 'No URL')}")
                print(f"Content Length: {len(content.get('content', ''))} characters")
                print()
                
                # Show first 500 characters of content
                content_text = content.get('content', '')
                if content_text:
                    print("📄 Content Preview (first 500 characters):")
                    print("-" * 40)
                    print(content_text[:500])
                    if len(content_text) > 500:
                        print("...")
                    print()
                else:
                    print("⚠️  No content text extracted")
                    
                return True, content
            else:
                print("❌ Failed to extract content")
                return False, None
                
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False, None

async def test_interviewing_io_extraction():
    """Test interviewing.io blog extraction."""
    print("\n🧪 Testing Interviewing.io Blog Extraction")
    print("=" * 60)
    
    blog_url = "https://interviewing.io/blog"
    
    print(f"Testing URL: {blog_url}")
    print()
    
    try:
        # Initialize components
        async with ContentExtractor() as extractor:
            print("✅ Content extractor initialized")
            
            # Extract content
            print("🔄 Extracting content...")
            start_time = time.time()
            
            content = await extractor.extract_content(blog_url)
            
            end_time = time.time()
            extraction_time = end_time - start_time
            
            if content:
                print(f"✅ Content extracted successfully in {extraction_time:.2f} seconds!")
                print()
                print("📊 Content Summary:")
                print("-" * 40)
                print(f"Title: {content.get('title', 'No title')}")
                print(f"Content Type: {content.get('content_type', 'Unknown')}")
                print(f"Author: {content.get('author', 'No author')}")
                print(f"URL: {content.get('url', 'No URL')}")
                print(f"Content Length: {len(content.get('content', ''))} characters")
                print()
                
                # Show first 500 characters of content
                content_text = content.get('content', '')
                if content_text:
                    print("📄 Content Preview (first 500 characters):")
                    print("-" * 40)
                    print(content_text[:500])
                    if len(content_text) > 500:
                        print("...")
                    print()
                else:
                    print("⚠️  No content text extracted")
                    
                return True, content
            else:
                print("❌ Failed to extract content")
                return False, None
                
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False, None

async def test_full_async_pipeline():
    """Test the full async pipeline with both URLs."""
    print("\n🧪 Testing Full Async Pipeline")
    print("=" * 60)
    
    urls = [
        "https://drive.google.com/file/d/10W-Wl8DMISmLe6z1GnTu09sEyuX9dnm6/view",
        "https://interviewing.io/blog"
    ]
    
    try:
        # Initialize all components
        async with ContentExtractor() as extractor, \
                   URLProcessor() as url_processor:
            
            # Initialize database handler separately (not async context manager)
            db_handler = DatabaseHandler()
            await db_handler.connect()
            
            # Initialize LLM processor
            llm_processor = LLMProcessor()
            
            print("✅ All components initialized")
            print()
            
            total_start_time = time.time()
            
            for i, url in enumerate(urls, 1):
                print(f"--- Processing URL {i}: {url} ---")
                
                try:
                    # Step 1: Discover subpages
                    print("🔍 Discovering subpages...")
                    subpages = await url_processor.discover_subpages(url)
                    print(f"   Found {len(subpages)} subpages")
                    
                    # Step 2: Extract content
                    print("📄 Extracting content...")
                    content_data = await extractor.extract_content(url)
                    
                    if content_data:
                        print(f"   ✅ Content extracted successfully")
                        print(f"   Title: {content_data.get('title', 'No title')}")
                        print(f"   Content Length: {len(content_data.get('content', ''))} characters")
                        
                        # Step 3: Validate content
                        print("🤖 Validating content...")
                        is_valid = await llm_processor.validate_content(content_data)
                        print(f"   Content valid: {is_valid}")
                        
                        if is_valid:
                            # Step 4: Process with LLM
                            print("🧠 Processing with LLM...")
                            knowledge_data = await llm_processor.process_content(
                                content_data, "test_team_123", "test_user"
                            )
                            
                            if knowledge_data:
                                print(f"   ✅ Knowledge extracted successfully")
                                print(f"   Items: {len(knowledge_data.get('items', []))}")
                                
                                # Step 5: Save to database
                                print("💾 Saving to database...")
                                success = await db_handler.save_knowledge_item(knowledge_data)
                                print(f"   Save successful: {success}")
                            else:
                                print(f"   ❌ Failed to extract knowledge")
                        else:
                            print(f"   ⚠️  Content not suitable for knowledge extraction")
                    else:
                        print(f"   ❌ Failed to extract content")
                        
                except Exception as e:
                    print(f"   ❌ Error processing {url}: {e}")
            
            total_end_time = time.time()
            total_time = total_end_time - total_start_time
            
            print(f"\n✅ Full pipeline completed in {total_time:.2f} seconds")
            
            # Clean up database connection
            await db_handler.disconnect()
            
    except Exception as e:
        print(f"❌ Full pipeline test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function."""
    print("🧪 Async URL Processing Tests")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run individual tests
    print("\n1. Testing Google Drive URL extraction...")
    google_success, google_content = asyncio.run(test_google_drive_extraction())
    
    print("\n2. Testing Interviewing.io blog extraction...")
    blog_success, blog_content = asyncio.run(test_interviewing_io_extraction())
    
    # Run full pipeline test
    print("\n3. Testing full async pipeline...")
    asyncio.run(test_full_async_pipeline())
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    print(f"Google Drive URL: {'✅ PASS' if google_success else '❌ FAIL'}")
    print(f"Interviewing.io Blog: {'✅ PASS' if blog_success else '❌ FAIL'}")
    
    if google_success and blog_success:
        print("\n🎉 All tests passed!")
        print("\nYou can now use the full async processing with:")
        print("python main.py urls.txt --team-id your_team_id --processing-mode async")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    main() 