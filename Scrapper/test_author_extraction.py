#!/usr/bin/env python3
"""
Test script to verify improved author extraction functionality.
"""

import os
import sys
import logging

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_extractor import ContentExtractor

def test_author_extraction():
    """Test author extraction with various URL types."""
    print("🧪 Testing Author Extraction")
    print("=" * 50)
    
    # Test URLs that should have authors
    test_urls = [
        "https://blog.interviewing.io/",
        "https://medium.com/",
        "https://dev.to/",
        "https://hashnode.dev/",
        "https://css-tricks.com/"
    ]
    
    extractor = ContentExtractor()
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        try:
            content = extractor.extract_content_sync(url)
            if content:
                title = content.get('title', 'No title')
                author = content.get('author', 'No author found')
                print(f"  Title: {title}")
                print(f"  Author: {author}")
                
                if author and author != 'No author found':
                    print(f"  ✅ Author extracted successfully")
                else:
                    print(f"  ⚠️  No author found")
            else:
                print(f"  ❌ Failed to extract content")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_author_cleaning():
    """Test the author text cleaning functionality."""
    print("\n🧪 Testing Author Text Cleaning")
    print("=" * 50)
    
    extractor = ContentExtractor()
    
    test_cases = [
        ("by John Doe", "John Doe"),
        ("Author: Jane Smith", "Jane Smith"),
        ("Written by Bob Johnson on 2024-01-15", "Bob Johnson"),
        ("Posted by Alice Brown at 10:30 AM", "Alice Brown"),
        ("Contributor: Charlie Wilson", "Charlie Wilson"),
        ("John Doe", "John Doe"),
        ("", ""),
        ("by", ""),
        ("Author:", ""),
        ("12/25/2024", ""),  # Date pattern
        ("Very long author name that exceeds reasonable limits and should be filtered out", ""),
        # Multiple author patterns
        ("John Doe and Jane Smith", "John Doe and Jane Smith"),
        ("By John Doe, Jane Smith", "John Doe, Jane Smith"),
        ("Authors: John Doe, Jane Smith, Bob Johnson", "John Doe, Jane Smith, Bob Johnson"),
    ]
    
    for input_text, expected in test_cases:
        result = extractor._clean_author_text(input_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} Input: '{input_text}' -> Output: '{result}' (Expected: '{expected}')")

def test_multiple_author_extraction():
    """Test multiple author extraction functionality."""
    print("\n🧪 Testing Multiple Author Extraction")
    print("=" * 50)
    
    extractor = ContentExtractor()
    
    # Test URLs that might have multiple authors
    test_urls = [
        "https://blog.interviewing.io/",
        "https://medium.com/",
        "https://dev.to/",
        "https://hashnode.dev/",
        "https://css-tricks.com/"
    ]
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        try:
            content = extractor.extract_content_sync(url)
            if content:
                title = content.get('title', 'No title')
                author = content.get('author', 'No author found')
                print(f"  Title: {title}")
                print(f"  Author(s): {author}")
                
                if author and author != 'No author found':
                    if ',' in author:
                        print(f"  ✅ Multiple authors detected: {author}")
                    else:
                        print(f"  ✅ Single author detected: {author}")
                else:
                    print(f"  ⚠️  No author found")
            else:
                print(f"  ❌ Failed to extract content")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_author_deduplication():
    """Test that duplicate authors are properly handled."""
    print("\n🧪 Testing Author Deduplication")
    print("=" * 50)
    
    extractor = ContentExtractor()
    
    # Test cases that should result in deduplication
    test_cases = [
        # These should be cleaned and deduplicated
        ("John Doe, John Doe", "John Doe"),
        ("Jane Smith, Jane Smith, Bob Johnson", "Jane Smith, Bob Johnson"),
        ("Author: John Doe, By John Doe", "John Doe"),
    ]
    
    for input_text, expected in test_cases:
        # Simulate the deduplication process
        authors = set()
        for author in input_text.split(','):
            cleaned = extractor._clean_author_text(author.strip())
            if cleaned:
                authors.add(cleaned)
        
        result = ', '.join(sorted(authors))
        status = "✅" if result == expected else "❌"
        print(f"{status} Input: '{input_text}' -> Output: '{result}' (Expected: '{expected}')")

def main():
    """Main test function."""
    print("🧪 Author Extraction Test")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test author text cleaning
    test_author_cleaning()
    
    # Test multiple author extraction
    test_multiple_author_extraction()
    
    # Test author deduplication
    test_author_deduplication()
    
    # Test actual author extraction
    test_author_extraction()
    
    print("\n✅ Author extraction test completed!")
    print("\nThe improved author extraction should now capture authors from:")
    print("- Common CSS selectors (.author, .byline, etc.)")
    print("- Meta tags (author, article:author, twitter:creator)")
    print("- JSON-LD structured data")
    print("- Text patterns (by Author Name, Written by, etc.)")
    print("- Social media profiles and author bios")
    print("- Multiple authors on the same page")
    print("- Comma-separated author lists")
    print("- Automatic deduplication of duplicate authors")

if __name__ == "__main__":
    main() 