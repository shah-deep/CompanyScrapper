# Knowledge Scraper

A powerful web scraping and knowledge extraction application that processes URLs, extracts technical content, and stores structured knowledge in MongoDB using Gemini AI and LangChain.

## Features

- **Parallel URL Processing**: Efficiently processes multiple URLs concurrently
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

- `MAX_CONCURRENT_REQUESTS`: Number of parallel requests (default: 5)
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
3. Processes each URL and discovers subpages
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

# Search existing knowledge
python main.py urls.txt --team-id your_team_id --search "python async"

# Show database statistics
python main.py urls.txt --team-id your_team_id --stats
```

### URL File Format

Create a text file with one URL per line:

```
https://example.com/blog/post1
https://example.com/blog/post2
https://example.com/guides/getting-started
```

## Iterative Processing Details

### File Management

When using `--iterative` mode:

- **Input file**: `abc.txt` (your original URLs)
- **Subpage file**: `abc_subpage.txt` (all discovered URLs)
- **Updated input file**: `abc.txt` (appended with new URLs)

### Processing Flow

1. **Initial Load**: Read URLs from input file
2. **Iteration Loop**:
   - Process current batch of URLs
   - Discover subpages for each URL
   - Save all discovered URLs to subpage file
   - Identify new URLs not in original file
   - Append new URLs to original file
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

============================================================
ITERATION 2
URLs to process in this iteration: 12
Total URLs processed so far: 3
============================================================
Discovered 8 subpages from https://example.com/blog/post1
Appended 5 new URLs to abc.txt

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
Subpage file: abc_subpage.txt
============================================================
```

## How It Works

1. **URL Loading**: Reads URLs from the specified text file
2. **Subpage Discovery**: For each URL, discovers related subpages and adds them to the queue
3. **Content Extraction**: Extracts content from each URL (HTML, PDF, or text)
4. **Content Validation**: Uses AI to validate if content is worth processing
5. **Knowledge Extraction**: Uses Gemini AI to extract structured technical knowledge
6. **Markdown Conversion**: Converts content to well-formatted Markdown
7. **Database Storage**: Saves structured knowledge to MongoDB
8. **Iterative Refinement**: (NEW!) Continues discovering and processing until no new content is found

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
- Iterative processing safeguards

## Logging

Logs are written to both:
- Console output
- Log file (configurable via `LOG_FILE` environment variable)

## Performance Considerations

- **Concurrency**: Configurable parallel processing
- **Rate Limiting**: Built-in request throttling
- **Content Filtering**: Skips non-technical content
- **Duplicate Detection**: Prevents processing the same URL multiple times
- **Smart URL Filtering**: Prioritizes content pages over utility pages
- **Iterative Efficiency**: Only processes new URLs in each iteration

## Testing

Run the test script to verify the iterative functionality:

```bash
python test_iterative.py
```

This will:
- Create a test URL file
- Run iterative processing
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

4. **Iterative Processing Issues**
   - Check file permissions for writing
   - Ensure sufficient disk space
   - Monitor memory usage for large URL sets

### Debug Mode

Enable debug logging by modifying the logging level in `main.py`:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

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