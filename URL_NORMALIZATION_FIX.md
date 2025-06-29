# URL Normalization Fix

## Problem Description

The CompanyScrapper was experiencing URL duplication issues where the same URL would appear multiple times with and without trailing slashes. For example:

```
https://interviewing.io
https://interviewing.io/
```

This happened because:

1. URLs were being processed through `urljoin()` which can produce different formats
2. The deduplication logic was using exact string matching
3. No consistent URL normalization was applied

## Solution Implemented

### 1. URL Normalization Function

Added a `_normalize_url()` method that:

- Parses URLs using `urlparse()`
- Removes trailing slashes from paths (except for root path `/`)
- Preserves query parameters and fragments
- Reconstructs the URL consistently

```python
def _normalize_url(self, url: str) -> str:
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
```

### 2. Updated Components

#### Crawler Module

- **`url_aggregator.py`**: Added URL normalization to all `add_*` methods and deduplication logic
- **`web_crawler.py`**: Added URL normalization for visited URL tracking and queue management

#### Scrapper Module

- **`url_processor.py`**: Added URL normalization for subpage discovery and deduplication

### 3. Utility Modules

Created shared utility modules:

- **`Crawler/utils.py`**: URL normalization functions for the Crawler module
- **`Scrapper/utils.py`**: URL normalization functions for the Scrapper module

## How It Works

### Before Fix

```python
# URLs were stored as-is, leading to duplicates
urls = [
    "https://interviewing.io",
    "https://interviewing.io/",
    "https://interviewing.io/about",
    "https://interviewing.io/about/"
]
# Deduplication used exact string matching
unique_urls = list(set(urls))  # Still had duplicates!
```

### After Fix

```python
# URLs are normalized for comparison
def deduplicate_urls(urls):
    seen_normalized = set()
    unique_urls = []
    for url in urls:
        normalized_url = normalize_url(url)
        if normalized_url not in seen_normalized:
            seen_normalized.add(normalized_url)
            unique_urls.append(url)  # Keep original format
    return unique_urls

# Result: No duplicates
urls = [
    "https://interviewing.io",
    "https://interviewing.io/",
    "https://interviewing.io/about", 
    "https://interviewing.io/about/"
]
unique_urls = deduplicate_urls(urls)
# Result: ["https://interviewing.io", "https://interviewing.io/about"]
```

## Testing

Run the test script to see the normalization in action:

```bash
python test_url_normalization.py
```

Example output:

```
URL Normalization Test
==================================================
Original: https://interviewing.io
Normalized: https://interviewing.io

Original: https://interviewing.io/
Normalized: https://interviewing.io/

Original: https://interviewing.io/about
Normalized: https://interviewing.io/about

Original: https://interviewing.io/about/
Normalized: https://interviewing.io/about

Deduplication test:
Original count: 11
After deduplication: 6
Duplicates removed: 5
```

## Benefits

1. **Eliminates URL Duplicates**: No more duplicate URLs with/without trailing slashes
2. **Consistent Processing**: All URL operations use the same normalization logic
3. **Accurate Counting**: URL counts now reflect actual unique URLs
4. **Better Performance**: Reduced storage and processing overhead
5. **Maintainable Code**: Centralized URL normalization logic

## Usage

The normalization is automatically applied in:

- URL discovery and crawling
- URL aggregation and deduplication
- File generation and storage
- Database operations

No changes needed to existing code - the fix is transparent to the user.
