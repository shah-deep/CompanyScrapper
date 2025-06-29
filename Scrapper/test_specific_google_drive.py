#!/usr/bin/env python3
"""
Test script to extract content from a specific Google Drive URL.
"""

import os
import sys
import logging
import asyncio

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_extractor import ContentExtractor

async def test_google_drive_url():
    """Test extraction from the specific Google Drive URL."""
    print("🧪 Testing Specific Google Drive URL")
    print("=" * 60)
    
    # The URL provided by the user
    test_url = "https://drive.google.com/file/d/10W-Wl8DMISmLe6z1GnTu09sEyuX9dnm6/view?usp=sharing"
    
    print(f"Testing URL: {test_url}")
    print()
    
    try:
        # Initialize the content extractor
        async with ContentExtractor() as extractor:
            print("✅ Content extractor initialized")
            
            # Check if it's detected as a Google Drive URL
            is_drive = extractor._is_google_drive_url(test_url)
            print(f"🔍 Detected as Google Drive URL: {is_drive}")
            
            if is_drive:
                # Extract file ID
                file_id = extractor._extract_google_drive_file_id(test_url)
                print(f"📁 Extracted file ID: {file_id}")
                
                # Build download URL
                if file_id:
                    download_url = extractor._build_google_drive_download_url(file_id)
                    print(f"⬇️  Download URL: {download_url}")
                else:
                    print("❌ Failed to extract file ID from Google Drive URL")
                print()
            
            # Extract content
            print("🔄 Extracting content...")
            content = await extractor.extract_content(test_url)
            
            if content:
                print("✅ Content extracted successfully!")
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
                    
            else:
                print("❌ Failed to extract content")
                
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function."""
    print("🧪 Google Drive URL Test")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the async test
    asyncio.run(test_google_drive_url())
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main() 