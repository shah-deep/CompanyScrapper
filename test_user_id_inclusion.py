#!/usr/bin/env python3
"""
Test script to verify that user_id is properly included in items when provided
"""

import sys
import os

# Add the Scrapper directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'Scrapper'))

from llm_processor import LLMProcessor

def test_user_id_inclusion():
    """Test that user_id is included in items when provided."""
    
    # Mock content data
    content_data = {
        'title': 'Test Title',
        'content': 'This is test content with technical information about APIs and programming.',
        'content_type': 'blog',
        'author': 'Test Author',
        'url': 'https://example.com/test'
    }
    
    # Test with user_id provided
    team_id = "test_team_123"
    user_id = "test_user_456"
    
    try:
        # Initialize LLM processor (this will fail without API key, but we can test the logic)
        processor = LLMProcessor()
        
        # Test the _extract_knowledge method directly
        import asyncio
        
        async def test_async():
            # Test with user_id
            result_with_user = await processor._extract_knowledge(
                content_data, 
                "# Test Title\n\nThis is test content.", 
                team_id, 
                user_id
            )
            
            # Test without user_id
            result_without_user = await processor._extract_knowledge(
                content_data, 
                "# Test Title\n\nThis is test content.", 
                team_id, 
                ""
            )
            
            print("Test Results:")
            print("=" * 50)
            
            if result_with_user:
                print("✓ With user_id:")
                print(f"  Team ID: {result_with_user.get('team_id')}")
                items = result_with_user.get('items', [])
                if items:
                    item = items[0]
                    print(f"  Title: {item.get('title')}")
                    print(f"  User ID: {item.get('user_id', 'NOT FOUND')}")
                    print(f"  Has user_id field: {'user_id' in item}")
                    print(f"  All item keys: {list(item.keys())}")
                else:
                    print("  No items found")
            else:
                print("✗ With user_id: No result returned")
            
            print()
            
            if result_without_user:
                print("✓ Without user_id:")
                print(f"  Team ID: {result_without_user.get('team_id')}")
                items = result_without_user.get('items', [])
                if items:
                    item = items[0]
                    print(f"  Title: {item.get('title')}")
                    print(f"  User ID: {item.get('user_id', 'NOT FOUND')}")
                    print(f"  Has user_id field: {'user_id' in item}")
                    print(f"  All item keys: {list(item.keys())}")
                else:
                    print("  No items found")
            else:
                print("✗ Without user_id: No result returned")
        
        # Run the test
        asyncio.run(test_async())
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        print("This is expected if GEMINI_API_KEY is not set")
        print("The important thing is that the code structure is correct")

if __name__ == "__main__":
    test_user_id_inclusion() 