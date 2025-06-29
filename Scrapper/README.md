# Knowledge Scraper

A powerful web scraping and knowledge extraction application that processes URLs, extracts technical content, and stores structured knowledge in MongoDB using Gemini AI and LangChain.

## Features

- **Parallel URL Processing**: Efficiently processes multiple URLs concurrently
- **Subpage Discovery**: Automatically discovers and processes subpages from main URLs
- **Multi-format Support**: Handles HTML pages, PDFs, and plain text files
- **AI-Powered Extraction**: Uses Gemini AI to extract and structure technical knowledge
- **Markdown Conversion**: Converts content to well-formatted Markdown
- **MongoDB Storage**: Stores structured knowledge in MongoDB Atlas
- **Content Validation**: Validates content quality before processing
- **Search Capabilities**: Search through stored knowledge

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

### Advanced Usage

```bash
# Process URLs and save discovered subpages back to file
python main.py urls.txt --team-id your_team_id --save-urls

# Process with specific user ID
python main.py urls.txt --team-id your_team_id --user-id user123

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

## How It Works

1. **URL Loading**: Reads URLs from the specified text file
2. **Subpage Discovery**: For each URL, discovers related subpages and adds them to the queue
3. **Content Extraction**: Extracts content from each URL (HTML, PDF, or text)
4. **Content Validation**: Uses AI to validate if content is worth processing
5. **Knowledge Extraction**: Uses Gemini AI to extract structured technical knowledge
6. **Markdown Conversion**: Converts content to well-formatted Markdown
7. **Database Storage**: Saves structured knowledge to MongoDB

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

## Logging

Logs are written to both:
- Console output
- Log file (configurable via `LOG_FILE` environment variable)

## Performance Considerations

- **Concurrency**: Configurable parallel processing
- **Rate Limiting**: Built-in request throttling
- **Content Filtering**: Skips non-technical content
- **Duplicate Detection**: Prevents processing the same URL multiple times

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