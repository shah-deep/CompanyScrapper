#!/usr/bin/env python3
"""
Test script to demonstrate and compare both processing modes.
"""

import os
import sys
import logging
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import KnowledgeScraper, setup_logging

def test_multiprocessing_mode():
    """Test multiprocessing mode."""
    print("🧪 Testing Multiprocessing Mode")
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
        start_time = time.time()
        
        # Initialize scraper with multiprocessing mode
        with KnowledgeScraper("test_team_123", "test_user", "multiprocessing") as scraper:
            print(f"✅ Process pool initialized with {scraper.max_workers} workers")
            
            # Test basic processing
            print("\n🚀 Starting multiprocessing processing...")
            stats = scraper.process_url_file(test_file, save_discovered_urls=False)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"✅ Processing completed in {processing_time:.2f} seconds")
            print(f"Statistics: {stats}")
            
            return True, processing_time
            
    except Exception as e:
        print(f"❌ Multiprocessing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, 0
    
    finally:
        # Cleanup test files
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"🧹 Cleaned up: {test_file}")

async def test_async_mode():
    """Test async mode."""
    print("\n🧪 Testing Async Mode")
    print("=" * 50)
    
    # Create a test URL file
    test_file = "test_async_urls.txt"
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
        start_time = time.time()
        
        # Initialize scraper with async mode
        async with KnowledgeScraper("test_team_123", "test_user", "async") as scraper:
            print("✅ Async components initialized")
            
            # Test basic processing
            print("\n🚀 Starting async processing...")
            stats = await scraper._process_url_file_async(test_file, save_discovered_urls=False)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"✅ Processing completed in {processing_time:.2f} seconds")
            print(f"Statistics: {stats}")
            
            return True, processing_time
            
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, 0
    
    finally:
        # Cleanup test files
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"🧹 Cleaned up: {test_file}")

def test_iterative_modes():
    """Test iterative processing in both modes."""
    print("\n🧪 Testing Iterative Processing in Both Modes")
    print("=" * 60)
    
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
    
    results = {}
    
    try:
        # Test multiprocessing iterative
        print("\n--- Multiprocessing Iterative ---")
        start_time = time.time()
        
        with KnowledgeScraper("test_team_123", "test_user", "multiprocessing") as scraper:
            stats = scraper.process_url_file_iterative(test_file)
            
        end_time = time.time()
        results['multiprocessing'] = {
            'success': True,
            'time': end_time - start_time,
            'stats': stats
        }
        print(f"✅ Completed in {results['multiprocessing']['time']:.2f} seconds")
        
    except Exception as e:
        print(f"❌ Multiprocessing iterative failed: {e}")
        results['multiprocessing'] = {'success': False, 'time': 0, 'stats': {}}
    
    try:
        # Test async iterative
        print("\n--- Async Iterative ---")
        import asyncio
        
        async def run_async_iterative():
            start_time = time.time()
            
            async with KnowledgeScraper("test_team_123", "test_user", "async") as scraper:
                stats = await scraper._process_url_file_iterative_async(test_file)
                
            end_time = time.time()
            return end_time - start_time, stats
        
        start_time = time.time()
        processing_time, stats = asyncio.run(run_async_iterative())
        
        results['async'] = {
            'success': True,
            'time': processing_time,
            'stats': stats
        }
        print(f"✅ Completed in {results['async']['time']:.2f} seconds")
        
    except Exception as e:
        print(f"❌ Async iterative failed: {e}")
        results['async'] = {'success': False, 'time': 0, 'stats': {}}
    
    finally:
        # Cleanup test files
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n🧹 Cleaned up: {test_file}")
        
        subpage_file = Path(test_file).parent / f"{Path(test_file).stem}_subpage{Path(test_file).suffix}"
        if subpage_file.exists():
            subpage_file.unlink()
            print(f"🧹 Cleaned up: {subpage_file}")
    
    return results

def main():
    """Main test function."""
    print("🧪 Knowledge Scraper - Processing Modes Test")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    
    # Test basic processing modes
    print("\n" + "=" * 60)
    print("📊 Basic Processing Mode Comparison")
    print("=" * 60)
    
    # Test multiprocessing
    mp_success, mp_time = test_multiprocessing_mode()
    
    # Test async
    import asyncio
    async_success, async_time = asyncio.run(test_async_mode())
    
    print("\n" + "=" * 60)
    print("📊 Basic Processing Results")
    print("=" * 60)
    
    if mp_success:
        print(f"Multiprocessing: ✅ PASS ({mp_time:.2f}s)")
    else:
        print("Multiprocessing: ❌ FAIL")
    
    if async_success:
        print(f"Async:          ✅ PASS ({async_time:.2f}s)")
    else:
        print("Async:          ❌ FAIL")
    
    if mp_success and async_success:
        if mp_time < async_time:
            print(f"\n🏆 Multiprocessing was {async_time/mp_time:.1f}x faster")
        else:
            print(f"\n🏆 Async was {mp_time/async_time:.1f}x faster")
    
    # Test iterative modes
    print("\n" + "=" * 60)
    print("📊 Iterative Processing Comparison")
    print("=" * 60)
    
    iterative_results = test_iterative_modes()
    
    print("\n" + "=" * 60)
    print("📊 Iterative Processing Results")
    print("=" * 60)
    
    for mode, result in iterative_results.items():
        if result['success']:
            print(f"{mode.capitalize()}: ✅ PASS ({result['time']:.2f}s)")
            print(f"  - URLs processed: {result['stats'].get('urls_processed', 0)}")
            print(f"  - Subpages discovered: {result['stats'].get('subpages_discovered', 0)}")
            print(f"  - Iterations: {result['stats'].get('iterations_completed', 0)}")
        else:
            print(f"{mode.capitalize()}: ❌ FAIL")
    
    print("\n✅ Processing modes test completed!")
    print("\nYou can now use either mode with:")
    print("python main.py urls.txt --team-id your_team_id --processing-mode multiprocessing")
    print("python main.py urls.txt --team-id your_team_id --processing-mode async")

if __name__ == "__main__":
    main() 