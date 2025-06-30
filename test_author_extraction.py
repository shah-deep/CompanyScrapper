#!/usr/bin/env python3
"""
Test script to verify author extraction from a specific URL
"""

import asyncio
import sys
import os

# Add the Scrapper directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'Scrapper'))

from content_extractor import ContentExtractor
from llm_processor import LLMProcessor

async def test_author_extraction():
    """Test author extraction from the provided URL"""
    url = "https://blog.alinelerner.com/what-i-learned-from-reading-8000-recruiting-messages"
    
    print(f"Testing author extraction for: {url}")
    print("=" * 80)
    
    # Step 1: Extract content and author from HTML
    async with ContentExtractor() as extractor:
        print("1. Extracting content from HTML...")
        content_data = await extractor.extract_content(url)
        
        if content_data:
            print(f"   Title: {content_data.get('title', 'N/A')}")
            print(f"   Author (from HTML): {content_data.get('author', 'N/A')}")
            print(f"   Content Type: {content_data.get('content_type', 'N/A')}")
            print(f"   Content Length: {len(content_data.get('content', ''))} characters")
            
            # Step 2: Test LLM metadata extraction
            print("\n2. Testing LLM metadata extraction...")
            llm_processor = LLMProcessor()
            
            # Convert to markdown
            markdown_content = await llm_processor._convert_to_markdown(content_data)
            
            # Extract metadata
            metadata_result = await llm_processor._extract_metadata_only(content_data, markdown_content)
            
            if metadata_result:
                title, content_type, author = metadata_result
                print(f"   LLM Title: {title}")
                print(f"   LLM Content Type: {content_type}")
                print(f"   LLM Author: {author}")
            else:
                print("   LLM metadata extraction failed")
            
            # Step 3: Test full knowledge extraction
            print("\n3. Testing full knowledge extraction...")
            knowledge_data = await llm_processor._extract_knowledge(content_data, markdown_content, "test_team", "test_user")
            
            if knowledge_data and knowledge_data.get('items'):
                item = knowledge_data['items'][0]
                print(f"   Final Title: {item.get('title', 'N/A')}")
                print(f"   Final Author: {item.get('author', 'N/A')}")
                print(f"   Final Content Type: {item.get('content_type', 'N/A')}")
            else:
                print("   Full knowledge extraction failed")
                
        else:
            print("Failed to extract content from URL")

if __name__ == "__main__":
    asyncio.run(test_author_extraction()) 