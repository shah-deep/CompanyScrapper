#!/usr/bin/env python3
"""
Debug script to see what content is being extracted and why LLM validation fails.
"""

import os
import sys
import logging
import asyncio

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_extractor import ContentExtractor
from llm_processor import LLMProcessor

async def debug_content_extraction():
    """Debug the content extraction and validation process."""
    print("🔍 Debugging Content Extraction and Validation")
    print("=" * 60)
    
    # The Google Drive URL
    test_url = "https://drive.google.com/file/d/10W-Wl8DMISmLe6z1GnTu09sEyuX9dnm6/view?usp=sharing"
    
    print(f"Testing URL: {test_url}")
    print()
    
    try:
        # Initialize components
        async with ContentExtractor() as extractor:
            print("✅ Content extractor initialized")
            
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
                
                # Show first 1000 characters of content to understand what we're working with
                content_text = content.get('content', '')
                if content_text:
                    print("📄 Content Preview (first 1000 characters):")
                    print("-" * 40)
                    print(content_text[:1000])
                    if len(content_text) > 1000:
                        print("...")
                    print()
                    
                    # Show last 500 characters to see the end
                    print("📄 Content Preview (last 500 characters):")
                    print("-" * 40)
                    print(content_text[-500:])
                    print()
                    
                    # Check for technical keywords
                    technical_keywords = [
                        'api', 'code', 'programming', 'development', 'software', 'technology',
                        'algorithm', 'database', 'framework', 'library', 'function', 'class',
                        'method', 'variable', 'loop', 'condition', 'error', 'debug', 'test',
                        'deploy', 'server', 'client', 'frontend', 'backend', 'database',
                        'security', 'performance', 'optimization', 'architecture', 'design',
                        'interview', 'coding', 'programming', 'technical', 'software'
                    ]
                    
                    content_lower = content_text.lower()
                    found_keywords = [keyword for keyword in technical_keywords if keyword in content_lower]
                    
                    print("🔍 Technical Keywords Found:")
                    print("-" * 40)
                    if found_keywords:
                        print(f"Found {len(found_keywords)} technical keywords:")
                        for keyword in found_keywords[:20]:  # Show first 20
                            print(f"  - {keyword}")
                        if len(found_keywords) > 20:
                            print(f"  ... and {len(found_keywords) - 20} more")
                    else:
                        print("No technical keywords found")
                    print()
                    
                    # Test LLM validation
                    print("🤖 Testing LLM Validation...")
                    llm_processor = LLMProcessor()
                    is_valid = await llm_processor.validate_content(content)
                    print(f"LLM Validation Result: {is_valid}")
                    
                    if not is_valid:
                        print("❌ Content rejected by LLM validator")
                        print("This is why nothing is being saved to the database.")
                        print()
                        print("💡 Solutions:")
                        print("1. The content might not be technical enough")
                        print("2. The LLM validator might be too strict")
                        print("3. You might need to adjust the validation criteria")
                    else:
                        print("✅ Content passed LLM validation")
                        
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
    print("🔍 Content Extraction Debug")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the async test
    asyncio.run(debug_content_extraction())
    
    print("\n✅ Debug completed!")

if __name__ == "__main__":
    main() 