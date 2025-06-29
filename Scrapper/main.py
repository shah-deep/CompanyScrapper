import asyncio
import logging
import os
import sys
from typing import List, Dict, Any
import argparse
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from url_processor import URLProcessor
from content_extractor import ContentExtractor
from llm_processor import LLMProcessor
from database_handler import DatabaseHandler
from config import Config

class KnowledgeScraper:
    def __init__(self, team_id: str, user_id: str = ""):
        self.team_id = team_id
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.url_processor = URLProcessor()
        self.content_extractor = ContentExtractor()
        self.llm_processor = LLMProcessor()
        self.db_handler = DatabaseHandler()
        
        # Statistics
        self.stats = {
            'urls_processed': 0,
            'urls_failed': 0,
            'subpages_discovered': 0,
            'content_extracted': 0,
            'knowledge_items_saved': 0,
            'errors': []
        }
    
    async def __aenter__(self):
        """Initialize all components."""
        await self.url_processor.__aenter__()
        await self.content_extractor.__aenter__()
        await self.db_handler.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up all components."""
        await self.url_processor.__aexit__(exc_type, exc_val, exc_tb)
        await self.content_extractor.__aexit__(exc_type, exc_val, exc_tb)
        await self.db_handler.disconnect()
    
    async def process_url_file(self, file_path: str, save_discovered_urls: bool = True) -> Dict[str, Any]:
        """Process URLs from a file and extract knowledge."""
        try:
            self.logger.info(f"Starting knowledge extraction for team: {self.team_id}")
            
            # Load URLs from file
            urls = self.url_processor.load_urls_from_file(file_path)
            if not urls:
                self.logger.error("No URLs found in file")
                return self.stats
            
            self.logger.info(f"Loaded {len(urls)} URLs from {file_path}")
            
            # Process URLs in parallel
            await self._process_urls_parallel()
            
            # Save discovered URLs back to file if requested
            if save_discovered_urls:
                all_urls = list(self.url_processor.processed_urls) + self.url_processor.url_queue
                self.url_processor.save_urls_to_file(file_path, all_urls)
                self.logger.info(f"Saved {len(all_urls)} URLs back to {file_path}")
            
            self.logger.info("Knowledge extraction completed")
            return self.stats
            
        except Exception as e:
            self.logger.error(f"Error processing URL file: {e}")
            self.stats['errors'].append(str(e))
            return self.stats
    
    async def _process_urls_parallel(self):
        """Process URLs in parallel with controlled concurrency."""
        semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_REQUESTS)
        
        tasks = []
        while True:
            url = self.url_processor.get_next_url()
            if not url:
                break
            
            task = asyncio.create_task(self._process_single_url(url, semaphore))
            tasks.append(task)
        
        # Wait for all tasks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_single_url(self, url: str, semaphore: asyncio.Semaphore):
        """Process a single URL with semaphore for concurrency control."""
        async with semaphore:
            try:
                self.logger.info(f"Processing URL: {url}")
                
                # Step 1: Discover subpages
                subpages = await self.url_processor.discover_subpages(url)
                if subpages:
                    self.url_processor.add_urls_to_queue(subpages)
                    self.stats['subpages_discovered'] += len(subpages)
                    self.logger.info(f"Discovered {len(subpages)} subpages from {url}")
                
                # Step 2: Extract content
                content_data = await self.content_extractor.extract_content(url)
                if not content_data:
                    self.stats['urls_failed'] += 1
                    self.logger.warning(f"Failed to extract content from {url}")
                    return
                
                self.stats['content_extracted'] += 1
                
                # Step 3: Validate content with LLM
                is_valid = await self.llm_processor.validate_content(content_data)
                if not is_valid:
                    self.logger.info(f"Content from {url} not suitable for knowledge extraction")
                    return
                
                # Step 4: Process content with LLM
                knowledge_data = await self.llm_processor.process_content(
                    content_data, self.team_id, self.user_id
                )
                if not knowledge_data:
                    self.logger.warning(f"Failed to process content with LLM for {url}")
                    return
                
                # Step 5: Save to database
                success = await self.db_handler.save_knowledge_item(knowledge_data)
                if success:
                    self.stats['knowledge_items_saved'] += len(knowledge_data.get('items', []))
                    self.logger.info(f"Saved knowledge item for {url}")
                else:
                    self.logger.error(f"Failed to save knowledge item for {url}")
                
                self.stats['urls_processed'] += 1
                
            except Exception as e:
                self.stats['urls_failed'] += 1
                self.stats['errors'].append(f"Error processing {url}: {str(e)}")
                self.logger.error(f"Error processing {url}: {e}")
    
    async def get_team_knowledge(self) -> Dict[str, Any]:
        """Retrieve all knowledge for the team."""
        return await self.db_handler.get_team_knowledge(self.team_id)
    
    async def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Search knowledge within the team."""
        return await self.db_handler.search_knowledge(self.team_id, query)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        db_stats = await self.db_handler.get_statistics()
        return {**self.stats, **db_stats}

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Knowledge Scraper for Technical Content')
    parser.add_argument('url_file', help='Path to file containing URLs (one per line)')
    parser.add_argument('--team-id', required=True, help='Team ID for organizing knowledge')
    parser.add_argument('--user-id', default='', help='User ID (optional)')
    parser.add_argument('--save-urls', action='store_true', help='Save discovered URLs back to file')
    parser.add_argument('--search', help='Search existing knowledge')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        async with KnowledgeScraper(args.team_id, args.user_id) as scraper:
            if args.search:
                # Search existing knowledge
                results = await scraper.search_knowledge(args.search)
                print(f"\nSearch results for '{args.search}':")
                for result in results:
                    print(f"Team: {result['team_id']}")
                    for item in result['items']:
                        print(f"  - {item['title']}")
                        print(f"    URL: {item['source_url']}")
                        print(f"    Type: {item['content_type']}")
                        print()
            
            elif args.stats:
                # Show statistics
                stats = await scraper.get_statistics()
                print("\nDatabase Statistics:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
            
            else:
                # Process URLs
                if not os.path.exists(args.url_file):
                    logger.error(f"URL file not found: {args.url_file}")
                    return
                
                stats = await scraper.process_url_file(args.url_file, args.save_urls)
                
                print("\nProcessing Statistics:")
                for key, value in stats.items():
                    if key != 'errors':
                        print(f"  {key}: {value}")
                
                if stats['errors']:
                    print("\nErrors:")
                    for error in stats['errors']:
                        print(f"  - {error}")
    
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 