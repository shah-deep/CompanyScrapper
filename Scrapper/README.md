# Knowledge Scraper

A powerful web scraping and knowledge extraction application that processes URLs, extracts technical content, and stores structured knowledge in MongoDB using Gemini AI and true multiprocessing.

## Features

- **True Parallel Processing**: Uses multiprocessing instead of threading for better CPU utilization
- **No Locks**: Each process works independently without shared state conflicts
- **Iterative Subpage Discovery**: Automatically discovers and processes subpages with iterative refinement
- **Subpage File Management**: Creates separate subpage files and tracks new discoveries
- **Multi-format Support**: Handles HTML pages, PDFs, and plain text files
- **AI-Powered Extraction**: Uses Gemini AI to extract and structure technical knowledge
- **Markdown Conversion**: Converts content to well-formatted Markdown
- **MongoDB Storage**: Stores structured knowledge in MongoDB Atlas
- **Content Validation**: Validates content quality before processing
- **Search Capabilities**: Search through stored knowledge
- **Enhanced URL Filtering**: Smart filtering to prioritize content pages

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Scrapper
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   - Copy `env_example.txt` to `.env`
   - Update the values with your actual credentials:
     - MongoDB Atlas connection string
     - Gemini API key
     - Other configuration options

## Configuration

### Required Environment Variables

- `MONGODB_URI`: Your MongoDB Atlas connection string
- `GEMINI_API_KEY`: Your Google Gemini API key
- `TEAM_ID`: Your team identifier for organizing knowledge

### Optional Configuration

- `MAX_CONCURRENT_REQUESTS`: Number of parallel processes (default: 5, max: CPU cores)
- `REQUEST_TIMEOUT`: Request timeout in seconds (default: 30)
- `MAX_CONTENT_LENGTH`: Maximum content length to process (default: 100000)

## Usage

### Basic Usage

Process URLs from a text file:

```bash
python main.py urls.txt --team-id your_team_id
```

### Iterative Subpage Discovery (NEW!)

Use the new iterative mode for comprehensive subpage discovery:

```bash
python main.py urls.txt --team-id your_team_id --iterative
```

**How it works:**
1. Loads URLs from the input file (e.g., `abc.txt`)
2. Creates a separate subpage file (e.g., `abc_subpage.txt`) for discovered URLs
3. Processes each URL and discovers subpages using multiprocessing
4. Identifies new URLs not in the original file
5. Appends new URLs to the original file
6. Repeats the process for new URLs until no new links are found
7. Continues until all discovered content is processed

### Advanced Usage

```bash
# Process URLs and save discovered subpages back to file
python main.py urls.txt --team-id your_team_id --save-urls

# Process with specific user ID
python main.py urls.txt --team-id your_team_id --user-id user123

# Use iterative mode for comprehensive discovery
python main.py urls.txt --team-id your_team_id --iterative

# Choose processing mode: multiprocessing (default) or async
python main.py urls.txt --team-id your_team_id --processing-mode multiprocessing
python main.py urls.txt --team-id your_team_id --processing-mode async

# Combine options
python main.py urls.txt --team-id your_team_id --iterative --processing-mode async

# Search existing knowledge
python main.py urls.txt --team-id your_team_id --search "python async"

# Show database statistics
python main.py urls.txt --team-id your_team_id --stats
```

## Processing Modes

The application supports two processing modes:

### 1. Multiprocessing Mode (Default)
- **True Parallelism**: Each URL is processed in a separate process
- **No GIL Limitations**: Bypasses Python's Global Interpreter Lock
- **Better CPU Utilization**: Utilizes all available CPU cores
- **Isolated Processing**: Each process has its own memory space
- **Fault Tolerance**: Process failures don't affect other processes
- **Best for**: CPU-intensive tasks, large URL sets, systems with multiple cores

### 2. Async Mode
- **Concurrent Processing**: Uses asyncio for non-blocking I/O operations
- **Lower Memory Usage**: Single process with multiple coroutines
- **Better for I/O-bound tasks**: Network requests, database operations
- **Simpler Resource Management**: No process pool overhead
- **Best for**: I/O-intensive tasks, smaller URL sets, memory-constrained systems

### Choosing the Right Mode

- **Use Multiprocessing** when:
  - You have multiple CPU cores available
  - Processing large numbers of URLs
  - Content extraction is CPU-intensive
  - You want maximum throughput

- **Use Async** when:
  - You're primarily doing I/O operations (network requests)
  - Memory is limited
  - Processing smaller URL sets
  - You want simpler resource management

### URL File Format

Create a text file with one URL per line:

```
https://example.com/blog/post1
https://example.com/blog/post2
https://example.com/guides/getting-started
```

## Multiprocessing Architecture

### Key Benefits

- **True Parallelism**: Each URL is processed in a separate process
- **No GIL Limitations**: Bypasses Python's Global Interpreter Lock
- **Better CPU Utilization**: Utilizes all available CPU cores
- **Isolated Processing**: Each process has its own memory space
- **Fault Tolerance**: Process failures don't affect other processes

### Process Pool Management

- **Dynamic Worker Count**: Automatically uses optimal number of workers (min of MAX_CONCURRENT_REQUESTS and CPU cores)
- **Resource Management**: Proper cleanup of process pools
- **Error Handling**: Graceful handling of process failures
- **Result Collection**: Efficient collection of results as they complete

## Iterative Processing Details

### File Management

When using `--iterative` mode:

- **Input file**: `abc.txt` (your original URLs)
- **Subpage file**: `abc_subpage.txt` (discovered URLs that haven't been added to original file yet)
- **Updated input file**: `abc.txt` (appended with new URLs)
- **Clean subpage file**: URLs are removed from subpage file when added to original file

### Processing Flow

1. **Initial Load**: Read URLs from input file
2. **Iteration Loop**:
   - Process current batch of URLs using multiprocessing
   - Discover subpages for each URL
   - Save all discovered URLs to subpage file
   - Identify new URLs not in original file
   - Append new URLs to original file
   - Remove newly added URLs from subpage file (keeps it clean)
   - Continue with new URLs in next iteration
3. **Termination**: Stop when no new URLs are found

### Example Output

```
============================================================
ITERATION 1
URLs to process in this iteration: 3
Total URLs processed so far: 0
============================================================
Discovered 15 subpages from https://example.com/blog
Appended 12 new URLs to abc.txt
Removed 12 URLs from subpage file abc_subpage.txt

============================================================
ITERATION 2
URLs to process in this iteration: 12
Total URLs processed so far: 3
============================================================
Discovered 8 subpages from https://example.com/blog/post1
Appended 5 new URLs to abc.txt
Removed 5 URLs from subpage file abc_subpage.txt

============================================================
ITERATION 3
URLs to process in this iteration: 5
Total URLs processed so far: 15
============================================================
No new URLs found. Stopping iterative process.

============================================================
ITERATIVE PROCESSING COMPLETED
Total iterations: 3
Total URLs processed: 20
Total subpages discovered: 28
Subpage file: abc_subpage.txt (contains only unprocessed discovered URLs)
============================================================
```

## How It Works

1. **URL Loading**: Reads URLs from the specified text file
2. **Process Pool Creation**: Initializes a pool of worker processes
3. **Parallel Processing**: Each URL is processed in a separate process
4. **Subpage Discovery**: For each URL, discovers related subpages
5. **Content Extraction**: Extracts content from each URL (HTML, PDF, or text)
6. **Content Validation**: Uses AI to validate if content is worth processing
7. **Knowledge Extraction**: Uses Gemini AI to extract structured technical knowledge
8. **Markdown Conversion**: Converts content to well-formatted Markdown
9. **Database Storage**: Saves structured knowledge to MongoDB
10. **Iterative Refinement**: Continues discovering and processing until no new content is found

## Output Format

The application stores knowledge in the following format:

```json
{
  "team_id": "your_team_id",
  "items": [
    {
      "title": "Item Title",
      "content": "Markdown formatted content",
      "content_type": "blog|podcast_transcript|call_transcript|linkedin_post|reddit_comment|book|other",
      "source_url": "https://example.com/post",
      "author": "Author Name",
      "user_id": "user123",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

## API Integration

### Gemini AI

The application uses Google's Gemini AI for:
- Content validation
- Knowledge extraction
- Markdown conversion

### MongoDB Atlas

Stores structured knowledge with:
- Team-based organization
- Full-text search capabilities
- Automatic indexing for performance

## Error Handling

The application includes comprehensive error handling:
- Network timeouts and connection errors
- Invalid content types
- API rate limiting
- Database connection issues
- Content processing failures
- Process failures and recovery
- Iterative processing safeguards

## Logging

Logs are written to both:
- Console output
- Log file (configurable via `LOG_FILE` environment variable)

## Performance Considerations

- **Multiprocessing**: True parallel processing without GIL limitations
- **CPU Optimization**: Automatically uses optimal number of processes
- **Memory Isolation**: Each process has independent memory space
- **Rate Limiting**: Built-in request throttling per process
- **Content Filtering**: Skips non-technical content
- **Duplicate Detection**: Prevents processing the same URL multiple times
- **Smart URL Filtering**: Prioritizes content pages over utility pages
- **Iterative Efficiency**: Only processes new URLs in each iteration

## Testing

Run the test script to verify the multiprocessing functionality:

```bash
python test_iterative.py
```

This will:
- Create a test URL file
- Run iterative processing with multiprocessing
- Show results and statistics
- Clean up test files

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Verify your connection string
   - Check network connectivity
   - Ensure MongoDB Atlas is accessible

2. **Gemini API Errors**
   - Verify your API key
   - Check API quota limits
   - Ensure proper API permissions

3. **Content Extraction Failures**
   - Check if URLs are accessible
   - Verify content type support
   - Review network connectivity

4. **Multiprocessing Issues**
   - Check system resources (CPU, memory)
   - Ensure proper file permissions
   - Monitor process pool size

5. **Iterative Processing Issues**
   - Check file permissions for writing
   - Ensure sufficient disk space
   - Monitor memory usage for large URL sets

### Debug Mode

Enable debug logging by modifying the logging level in `main.py`:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

### Performance Tuning

- **Adjust MAX_CONCURRENT_REQUESTS**: Set based on your CPU cores and system resources
- **Monitor Memory Usage**: Each process uses additional memory
- **Network Bandwidth**: Consider your network capacity when setting process count
- **API Rate Limits**: Ensure you don't exceed API quotas with multiple processes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the logs for error details 