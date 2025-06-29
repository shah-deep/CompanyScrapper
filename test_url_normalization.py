#!/usr/bin/env python3
"""
Test script to demonstrate URL normalization functionality
"""

from urllib.parse import urlparse

def normalize_url(url: str) -> str:
    """Normalize URL to handle trailing slashes consistently."""
    if not url:
        return url
    
    # Parse the URL
    parsed = urlparse(url)
    
    # Normalize the path - remove trailing slash unless it's the root path
    path = parsed.path
    if path.endswith('/') and len(path) > 1:
        path = path.rstrip('/')
    
    # Reconstruct the URL
    normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    if parsed.fragment:
        normalized += f"#{parsed.fragment}"
    
    return normalized

def test_url_normalization():
    """Test URL normalization with various examples."""
    
    # Test cases
    test_urls = [
        "https://interviewing.io",
        "https://interviewing.io/",
        "https://interviewing.io/about",
        "https://interviewing.io/about/",
        "https://interviewing.io/blog/post-1",
        "https://interviewing.io/blog/post-1/",
        "https://interviewing.io/",  # Root with slash
        "https://example.com/path?param=value",
        "https://example.com/path/?param=value",
        "https://example.com/path#fragment",
        "https://example.com/path/#fragment",
    ]
    
    print("URL Normalization Test")
    print("=" * 50)
    
    # Test individual normalization
    print("Individual URL normalization:")
    for url in test_urls:
        normalized = normalize_url(url)
        print(f"Original: {url}")
        print(f"Normalized: {normalized}")
        print()
    
    # Test deduplication
    print("Deduplication test:")
    print("Original URLs:")
    for url in test_urls:
        print(f"  {url}")
    
    # Simulate deduplication using normalized URLs
    seen_normalized = set()
    unique_urls = []
    for url in test_urls:
        normalized_url = normalize_url(url)
        if normalized_url not in seen_normalized:
            seen_normalized.add(normalized_url)
            unique_urls.append(url)
    
    print(f"\nAfter deduplication (using normalized URLs):")
    for url in unique_urls:
        print(f"  {url}")
    
    print(f"\nOriginal count: {len(test_urls)}")
    print(f"After deduplication: {len(unique_urls)}")
    print(f"Duplicates removed: {len(test_urls) - len(unique_urls)}")

if __name__ == "__main__":
    test_url_normalization() 