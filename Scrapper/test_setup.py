#!/usr/bin/env python3
"""
Test script to verify the setup of the Knowledge Scraper.
This script tests all major components without actually scraping content.
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from url_processor import URLProcessor
from content_extractor import ContentExtractor
from llm_processor import LLMProcessor
from database_handler import DatabaseHandler

def setup_logging():
    """Setup basic logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

async def test_config():
    """Test configuration loading."""
    print("🔧 Testing Configuration...")
    
    # Test environment variables
    required_vars = ['GEMINI_API_KEY', 'MONGODB_URI']
    missing_vars = []
    
    for var in required_vars:
        if not getattr(Config, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please check your .env file and ensure all required variables are set.")
        return False
    else:
        print("✅ Configuration loaded successfully")
        return True

async def test_url_processor():
    """Test URL processor initialization."""
    print("\n🌐 Testing URL Processor...")
    
    try:
        async with URLProcessor() as processor:
            # Test basic functionality
            test_urls = ["https://example.com", "https://test.com"]
            processor.add_urls_to_queue(test_urls)
            
            status = processor.get_queue_status()
            if status['queue_length'] == 2:
                print("✅ URL Processor working correctly")
                return True
            else:
                print("❌ URL Processor queue not working correctly")
                return False
                
    except Exception as e:
        print(f"❌ URL Processor test failed: {e}")
        return False

async def test_content_extractor():
    """Test content extractor initialization."""
    print("\n📄 Testing Content Extractor...")
    
    try:
        async with ContentExtractor() as extractor:
            print("✅ Content Extractor initialized successfully")
            return True
            
    except Exception as e:
        print(f"❌ Content Extractor test failed: {e}")
        return False

async def test_llm_processor():
    """Test LLM processor initialization."""
    print("\n🤖 Testing LLM Processor...")
    
    try:
        llm = LLMProcessor()
        print("✅ LLM Processor initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ LLM Processor test failed: {e}")
        return False

async def test_database_connection():
    """Test MongoDB connection."""
    print("\n🗄️ Testing Database Connection...")
    
    try:
        db_handler = DatabaseHandler()
        await db_handler.connect()
        
        # Test basic operations
        stats = await db_handler.get_statistics()
        print(f"✅ Database connected successfully")
        print(f"   - Database: {stats.get('database_name', 'Unknown')}")
        print(f"   - Collection: {stats.get('collection_name', 'Unknown')}")
        print(f"   - Total teams: {stats.get('total_teams', 0)}")
        print(f"   - Total items: {stats.get('total_items', 0)}")
        
        await db_handler.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

async def test_gemini_api():
    """Test Gemini API connection."""
    print("\n🧠 Testing Gemini API...")
    
    try:
        llm = LLMProcessor()
        
        # Test with a simple prompt
        test_content = {
            'title': 'Test Content',
            'content': 'This is a test content for validation.',
            'content_type': 'blog'
        }
        
        is_valid = await llm.validate_content(test_content)
        print(f"✅ Gemini API working correctly (validation result: {is_valid})")
        return True
        
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Knowledge Scraper Setup Test")
    print("=" * 50)
    
    setup_logging()
    
    tests = [
        test_config,
        test_url_processor,
        test_content_extractor,
        test_llm_processor,
        test_database_connection,
        test_gemini_api
    ]
    
    results = []
    
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    test_names = [
        "Configuration",
        "URL Processor", 
        "Content Extractor",
        "LLM Processor",
        "Database Connection",
        "Gemini API"
    ]
    
    passed = 0
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Your setup is ready to use.")
        print("\nYou can now run the scraper with:")
        print("python main.py sample_urls.txt --team-id your_team_id")
    else:
        print("⚠️  Some tests failed. Please check the configuration and try again.")
        print("\nCommon issues:")
        print("- Missing or incorrect environment variables")
        print("- Network connectivity issues")
        print("- Invalid API keys")
        print("- MongoDB connection string issues")

if __name__ == "__main__":
    asyncio.run(main()) 