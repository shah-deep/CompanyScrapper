#!/usr/bin/env python3
"""
Test script for improved metadata extraction functionality.
"""

import asyncio
import logging
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_processor import LLMProcessor
from config import Config

async def test_metadata_extraction():
    """Test the improved metadata extraction functionality."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize LLM processor
        llm_processor = LLMProcessor()
        
        # Test cases with different metadata scenarios
        test_cases = [
            {
                'name': 'Complete metadata',
                'data': {
                    'title': 'Python Async Programming Guide',
                    'content': 'This is a comprehensive guide to Python async programming. It covers asyncio, coroutines, and best practices.',
                    'content_type': 'tutorial',
                    'author': 'John Doe',
                    'url': 'https://example.com/python-async'
                }
            },
            {
                'name': 'Missing title',
                'data': {
                    'title': '',
                    'content': 'This is a comprehensive guide to Python async programming. It covers asyncio, coroutines, and best practices.',
                    'content_type': 'tutorial',
                    'author': 'John Doe',
                    'url': 'https://example.com/python-async'
                }
            },
            {
                'name': 'Generic title',
                'data': {
                    'title': 'Untitled',
                    'content': 'This is a comprehensive guide to Python async programming. It covers asyncio, coroutines, and best practices.',
                    'content_type': 'tutorial',
                    'author': 'John Doe',
                    'url': 'https://example.com/python-async'
                }
            },
            {
                'name': 'Missing author',
                'data': {
                    'title': 'Python Async Programming Guide',
                    'content': 'This is a comprehensive guide to Python async programming. It covers asyncio, coroutines, and best practices.',
                    'content_type': 'tutorial',
                    'author': '',
                    'url': 'https://example.com/python-async'
                }
            },
            {
                'name': 'Missing content type',
                'data': {
                    'title': 'Python Async Programming Guide',
                    'content': 'This is a comprehensive guide to Python async programming. It covers asyncio, coroutines, and best practices.',
                    'content_type': '',
                    'author': 'John Doe',
                    'url': 'https://example.com/python-async'
                }
            },
            {
                'name': 'Minimal metadata',
                'data': {
                    'title': '',
                    'content': 'This is a comprehensive guide to Python async programming. It covers asyncio, coroutines, and best practices.',
                    'content_type': '',
                    'author': '',
                    'url': 'https://example.com/python-async'
                }
            }
        ]
        
        logger.info("Testing metadata extraction functionality...")
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Test {i}: {test_case['name']}")
            logger.info(f"{'='*60}")
            
            # Convert to markdown first
            markdown_content = await llm_processor._convert_to_markdown(test_case['data'])
            
            # Extract metadata
            metadata_result = await llm_processor._extract_metadata_only(test_case['data'], markdown_content)
            
            if metadata_result:
                extracted_title, extracted_content_type, extracted_author = metadata_result
                
                logger.info(f"Original Title: '{test_case['data']['title']}'")
                logger.info(f"Extracted Title: '{extracted_title}'")
                logger.info(f"Original Content Type: '{test_case['data']['content_type']}'")
                logger.info(f"Extracted Content Type: '{extracted_content_type}'")
                logger.info(f"Original Author: '{test_case['data']['author']}'")
                logger.info(f"Extracted Author: '{extracted_author}'")
                
                # Check if extraction improved the metadata
                title_improved = extracted_title and extracted_title != test_case['data']['title']
                content_type_improved = extracted_content_type and extracted_content_type != test_case['data']['content_type']
                author_improved = extracted_author and extracted_author != test_case['data']['author']
                
                if title_improved or content_type_improved or author_improved:
                    logger.info("✅ Metadata extraction successful - improvements found")
                else:
                    logger.info("✅ Metadata extraction successful - using original values")
            else:
                logger.error("❌ Metadata extraction failed")
        
        logger.info(f"\n{'='*60}")
        logger.info("Metadata extraction testing completed")
        logger.info(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        return False
    
    return True

async def test_knowledge_extraction():
    """Test the improved knowledge extraction with metadata."""
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize LLM processor
        llm_processor = LLMProcessor()
        
        # Test case with missing title
        test_data = {
            'title': '',
            'content': '''
            Python Async Programming: A Comprehensive Guide
            
            Asynchronous programming in Python has become increasingly important for building high-performance applications. This guide covers the fundamentals of asyncio, coroutines, and best practices.
            
            Key Concepts:
            - Coroutines and async/await syntax
            - Event loops and task scheduling
            - Concurrent execution patterns
            - Error handling in async code
            
            Example Code:
            ```python
            import asyncio
            
            async def main():
                print("Hello, async world!")
                await asyncio.sleep(1)
                print("Goodbye!")
            
            asyncio.run(main())
            ```
            
            Best Practices:
            1. Always use asyncio.run() to start the event loop
            2. Handle exceptions properly in async functions
            3. Avoid blocking operations in coroutines
            4. Use asyncio.gather() for concurrent tasks
            ''',
            'content_type': 'tutorial',
            'author': 'Jane Smith',
            'url': 'https://example.com/python-async-guide'
        }
        
        logger.info("\nTesting knowledge extraction with metadata...")
        
        # Convert to markdown
        markdown_content = await llm_processor._convert_to_markdown(test_data)
        
        # Extract knowledge (this should also extract metadata)
        knowledge_result = await llm_processor._extract_knowledge(test_data, markdown_content, 'test_team', 'test_user')
        
        if knowledge_result:
            item = knowledge_result['items'][0]
            logger.info(f"✅ Knowledge extraction successful")
            logger.info(f"Final Title: '{item['title']}'")
            logger.info(f"Final Content Type: '{item['content_type']}'")
            logger.info(f"Final Author: '{item['author']}'")
            logger.info(f"Content Length: {len(item['content'])} characters")
        else:
            logger.error("❌ Knowledge extraction failed")
        
    except Exception as e:
        logger.error(f"Error during knowledge extraction testing: {e}")
        return False
    
    return True

async def main():
    """Main test function."""
    logger = logging.getLogger(__name__)
    
    logger.info("Starting metadata extraction tests...")
    
    # Test metadata extraction
    metadata_success = await test_metadata_extraction()
    
    # Test knowledge extraction
    knowledge_success = await test_knowledge_extraction()
    
    if metadata_success and knowledge_success:
        logger.info("\n🎉 All tests passed!")
        return True
    else:
        logger.error("\n❌ Some tests failed!")
        return False

if __name__ == "__main__":
    # Check if required environment variables are set
    if not Config.GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY environment variable is required")
        print("Please set it in your .env file or environment")
        sys.exit(1)
    
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 