#!/usr/bin/env python3
"""
Test script to verify content extraction works in multiprocessing environment.
"""

import os
import sys
import logging

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_extractor import ContentExtractor
from url_processor import URLProcessor
from main import process_single_url_worker

def test_content_extraction():
    """Test content extraction functionality."""
    print("🧪 Testing Content Extraction")
    print("=" * 50)
    
    # Test URL that was failing
    test_url = "https://interviewing.io/blog"
    
    print(f"Testing URL: {test_url}")
    
    try:
        # Test the worker function directly
        result = process_single_url_worker(test_url, "test_team", "test_user")
        
        print("✅ Worker function executed successfully")
        print(f"Result: {result}")
        
        if result.get('error'):
            print(f"❌ Error: {result['error']}")
            return False
        else:
            print("✅ Content extraction completed successfully")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_components():
    """Test individual components."""
    print("\n🧪 Testing Individual Components")
    print("=" * 50)
    
    test_url = "https://httpbin.org/html"
    
    try:
        # Test URL processor
        print("Testing URL processor...")
        url_processor = URLProcessor()
        subpages = url_processor.discover_subpages_sync(test_url)
        print(f"✅ URL processor: Found {len(subpages)} subpages")
        
        # Test content extractor
        print("Testing content extractor...")
        content_extractor = ContentExtractor()
        content = content_extractor.extract_content_sync(test_url)
        if content:
            print(f"✅ Content extractor: Extracted content with title '{content.get('title', 'No title')}'")
        else:
            print("❌ Content extractor: Failed to extract content")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🧪 Content Extraction Test")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    tests = [
        test_individual_components,
        test_content_extraction
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    test_names = [
        "Individual Components",
        "Content Extraction"
    ]
    
    passed = 0
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All content extraction tests passed!")
        print("\nThe multiprocessing content extraction is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the configuration and try again.")

if __name__ == "__main__":
    main() 