#!/usr/bin/env python3
"""
Test script for multiprocessing functionality.
This script tests the new multiprocessing approach.
"""

import os
import sys
import logging
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import KnowledgeScraper, setup_logging, process_single_url_worker

def test_multiprocessing_worker():
    """Test the individual worker function."""
    print("🧪 Testing Multiprocessing Worker")
    print("=" * 50)
    
    # Test with a simple URL
    test_url = "https://httpbin.org/html"
    team_id = "test_team"
    user_id = "test_user"
    
    print(f"Testing worker with URL: {test_url}")
    
    try:
        result = process_single_url_worker(test_url, team_id, user_id)
        
        print("✅ Worker function executed successfully")
        print(f"Result: {result}")
        
        if result.get('error'):
            print(f"⚠️  Worker returned error: {result['error']}")
        else:
            print("✅ Worker completed without errors")
            
        return True
        
    except Exception as e:
        print(f"❌ Worker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_process_pool():
    """Test the process pool functionality."""
    print("\n🧪 Testing Process Pool")
    print("=" * 50)
    
    # Create a test URL file
    test_file = "test_multiprocessing_urls.txt"
    test_urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/json",
        "https://httpbin.org/xml"
    ]
    
    # Write test URLs to file
    with open(test_file, 'w') as f:
        for url in test_urls:
            f.write(f"{url}\n")
    
    print(f"Created test file: {test_file}")
    print(f"Test URLs: {test_urls}")
    
    try:
        # Initialize scraper with test team ID
        with KnowledgeScraper("test_team_123", "test_user") as scraper:
            print(f"✅ Process pool initialized with {scraper.max_workers} workers")
            
            # Test basic processing
            print("\n🚀 Starting basic processing...")
            start_time = time.time()
            
            scraper._process_urls_parallel(test_urls)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"✅ Processing completed in {processing_time:.2f} seconds")
            print(f"Statistics: {scraper.get_statistics()}")
            
            return True
            
    except Exception as e:
        print(f"❌ Process pool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup test files
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"🧹 Cleaned up: {test_file}")

def test_iterative_multiprocessing():
    """Test iterative processing with multiprocessing."""
    print("\n🧪 Testing Iterative Multiprocessing")
    print("=" * 50)
    
    # Create a test URL file
    test_file = "test_iterative_urls.txt"
    test_urls = [
        "https://httpbin.org/html"
    ]
    
    # Write test URLs to file
    with open(test_file, 'w') as f:
        for url in test_urls:
            f.write(f"{url}\n")
    
    print(f"Created test file: {test_file}")
    print(f"Test URLs: {test_urls}")
    
    try:
        # Initialize scraper with test team ID
        with KnowledgeScraper("test_team_123", "test_user") as scraper:
            print("\n🚀 Starting iterative processing...")
            start_time = time.time()
            
            # Run iterative processing
            stats = scraper.process_url_file_iterative(test_file)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"\n✅ Iterative processing completed in {processing_time:.2f} seconds")
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
            else:
                print(f"\n⚠️  Subpage file not found: {subpage_file}")
            
            return True
            
    except Exception as e:
        print(f"❌ Iterative multiprocessing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
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
    """Main test function."""
    print("🧪 Knowledge Scraper - Multiprocessing Test")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    
    tests = [
        test_multiprocessing_worker,
        test_process_pool,
        test_iterative_multiprocessing
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
        "Multiprocessing Worker",
        "Process Pool",
        "Iterative Multiprocessing"
    ]
    
    passed = 0
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All multiprocessing tests passed!")
        print("\nThe multiprocessing implementation is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the configuration and try again.")

if __name__ == "__main__":
    main() 