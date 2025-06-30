import multiprocessing as mp
import logging
import os
import sys
from typing import List, Dict, Any, Set
import argparse
from pathlib import Path
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import asyncio
from logging.handlers import QueueHandler, QueueListener

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from url_processor import URLProcessor
from content_extractor import ContentExtractor
from llm_processor import LLMProcessor
from database_handler import DatabaseHandler
from config import Config

def setup_logging_queue(logfile=None):
    """Setup multiprocessing-safe logging to a single file."""
    if logfile is None:
        logfile = Config.LOG_FILE
    log_queue = mp.Queue(-1)
    file_handler = logging.FileHandler(logfile)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    listener = QueueListener(log_queue, file_handler)
    listener.start()
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = []
    root.addHandler(QueueHandler(log_queue))
    # Suppress noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    return listener, log_queue

def worker_init_logging(log_queue):
    """Initialize logging in worker processes to use the shared log queue."""
    root = logging.getLogger()
    root.handlers = []
    root.addHandler(QueueHandler(log_queue))
    root.setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)

class KnowledgeScraper:
    def __init__(self, team_id: str, user_id: str = "", processing_mode: str = "multiprocessing", skip_existing_urls: bool = False, log_queue=None):
        self.team_id = team_id
        self.user_id = user_id
        self.processing_mode = processing_mode.lower()  # "multiprocessing" or "async"
        self.skip_existing_urls = skip_existing_urls  # New parameter to skip URLs already in DB
        self.logger = logging.getLogger(__name__)
        self.log_queue = log_queue
        
        # Statistics
        self.stats = {
            'urls_processed': 0,
            'urls_failed': 0,
            'urls_skipped': 0,  # New stat for skipped URLs
            'subpages_discovered': 0,
            'content_extracted': 0,
            'knowledge_items_saved': 0,
            'iterations_completed': 0,
            'total_new_links_found': 0,
            'errors': []
        }
        
        # Track original URLs and discovered URLs
        self.original_urls: Set[str] = set()
        self.all_discovered_urls: Set[str] = set()
        
        # Cache for existing URLs from database
        self.existing_urls_from_db: Set[str] = set()
        
        # Process pool for parallel processing (only for multiprocessing mode)
        self.process_pool = None
        self.max_workers = min(Config.MAX_CONCURRENT_REQUESTS, mp.cpu_count())
        
        # Async components (only for async mode)
        self.url_processor = None
        self.content_extractor = None
        self.llm_processor = None
        self.db_handler = None
    
    def __enter__(self):
        """Initialize based on processing mode."""
        if self.processing_mode == "multiprocessing":
            # Setup process pool with logging queue
            if self.log_queue is not None:
                self.process_pool = mp.get_context("spawn").Pool(
                    processes=self.max_workers,
                    initializer=worker_init_logging,
                    initargs=(self.log_queue,)
                )
            else:
                self.process_pool = mp.get_context("spawn").Pool(processes=self.max_workers)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up based on processing mode."""
        if self.processing_mode == "multiprocessing" and self.process_pool:
            self.process_pool.close()
            self.process_pool.join()
        
        # Clean up shared database connection pool
        DatabaseHandler.close_connection_pool()
    
    async def __aenter__(self):
        """Initialize async components."""
        if self.processing_mode == "async":
            self.url_processor = URLProcessor()
            self.content_extractor = ContentExtractor()
            self.llm_processor = LLMProcessor()
            self.db_handler = DatabaseHandler()
            
            await self.url_processor.__aenter__()
            await self.content_extractor.__aenter__()
            await self.db_handler.connect()
            
            # Load existing URLs from database if skip_existing_urls is enabled
            await self._load_existing_urls_from_db()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up async components."""
        if self.processing_mode == "async":
            if self.url_processor:
                await self.url_processor.__aexit__(exc_type, exc_val, exc_tb)
            if self.content_extractor:
                await self.content_extractor.__aexit__(exc_type, exc_val, exc_tb)
            if self.db_handler:
                await self.db_handler.disconnect()
        
        # Clean up shared database connection pool
        DatabaseHandler.close_connection_pool()
    
    def _get_subpage_file_path(self, original_file_path: str) -> str:
        """Generate subpage file path based on original file path."""
        path = Path(original_file_path)
        subpage_path = path.parent / f"{path.stem}_subpage{path.suffix}"
        return str(subpage_path)
    
    def _load_urls_from_file(self, file_path: str) -> Set[str]:
        """Load URLs from file and return as a set."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                urls = {line.strip() for line in file if line.strip()}
            self.logger.info(f"Loaded {len(urls)} URLs from {file_path}")
            return urls
        except FileNotFoundError:
            self.logger.warning(f"File not found: {file_path}")
            return set()
        except Exception as e:
            self.logger.error(f"Error loading URLs from file {file_path}: {e}")
            return set()
    
    def _save_urls_to_file(self, file_path: str, urls: Set[str]):
        """Save URLs to file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                for url in sorted(urls):
                    file.write(f"{url}\n")
            self.logger.info(f"SAVED {len(urls)} URLs to {os.path.basename(file_path)}")
        except Exception as e:
            self.logger.error(f"Error saving URLs to file {file_path}: {e}")
    
    def _append_urls_to_file(self, file_path: str, urls: Set[str]):
        """Append URLs to existing file."""
        try:
            existing_urls = self._load_urls_from_file(file_path)
            new_urls = urls - existing_urls
            
            if new_urls:
                with open(file_path, 'a', encoding='utf-8') as file:
                    for url in sorted(new_urls):
                        file.write(f"{url}\n")
                self.logger.info(f"APPENDED {len(new_urls)} URLs to {os.path.basename(file_path)}")
                return len(new_urls)
            return 0
        except Exception as e:
            self.logger.error(f"Error appending URLs to file {file_path}: {e}")
            return 0
    
    def _remove_urls_from_subpage_file(self, file_path: str, urls: Set[str]):
        """Remove URLs from subpage file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                existing_urls = {line.strip() for line in file if line.strip()}
            
            new_urls = existing_urls - urls
            
            with open(file_path, 'w', encoding='utf-8') as file:
                for url in sorted(new_urls):
                    file.write(f"{url}\n")
            self.logger.info(f"Removed {len(urls)} URLs from subpage file {file_path}")
        except Exception as e:
            self.logger.error(f"Error removing URLs from subpage file {file_path}: {e}")
    
    def _delete_subpage_file(self, file_path: str):
        """Delete subpage file after processing is complete."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"DELETED subpage file: {os.path.basename(file_path)}")
        except Exception as e:
            self.logger.error(f"Error deleting subpage file {file_path}: {e}")
    
    async def _load_existing_urls_from_db(self):
        """Load existing URLs from database for the team to avoid reprocessing."""
        if not self.skip_existing_urls:
            return
        
        try:
            if self.processing_mode == "async":
                if not self.db_handler:
                    self.logger.warning("Database handler not initialized for async mode")
                    return
                
                team_data = await self.db_handler.get_team_knowledge(self.team_id)
                if team_data and 'items' in team_data:
                    existing_urls = {item.get('source_url', '') for item in team_data['items'] if item.get('source_url')}
                    self.existing_urls_from_db = existing_urls
                    self.logger.info(f"Loaded {len(existing_urls)} existing URLs from database for team {self.team_id}")
                else:
                    self.logger.info(f"No existing data found for team {self.team_id}")
            else:
                # For multiprocessing mode, we'll load this in the worker function
                pass
                
        except Exception as e:
            self.logger.error(f"Error loading existing URLs from database: {e}")
    
    def _load_existing_urls_from_db_sync(self):
        """Synchronous version of loading existing URLs from database."""
        if not self.skip_existing_urls:
            return
        
        try:
            # Create a temporary database handler for this process
            temp_handler = DatabaseHandler()
            
            # Create a new event loop for this thread/process
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            try:
                # Connect and get team data
                loop.run_until_complete(temp_handler.connect())
                team_data = loop.run_until_complete(temp_handler.get_team_knowledge(self.team_id))
                
                if team_data and 'items' in team_data:
                    existing_urls = {item.get('source_url', '') for item in team_data['items'] if item.get('source_url')}
                    self.existing_urls_from_db = existing_urls
                    self.logger.info(f"Loaded {len(existing_urls)} existing URLs from database for team {self.team_id}")
                else:
                    self.logger.info(f"No existing data found for team {self.team_id}")
                
                # Clean up
                loop.run_until_complete(temp_handler.disconnect())
                
            finally:
                if loop.is_running():
                    loop.close()
                    
        except Exception as e:
            self.logger.error(f"Error loading existing URLs from database: {e}")
    
    def _should_skip_url(self, url: str) -> bool:
        """Check if URL should be skipped because it already exists in database."""
        if not self.skip_existing_urls:
            return False
        
        return url in self.existing_urls_from_db
    
    def process_url_file_iterative(self, file_path: str) -> Dict[str, Any]:
        """Process URLs from a file with iterative subpage discovery using multiprocessing."""
        if self.processing_mode == "async":
            import asyncio
            return asyncio.run(self._process_url_file_iterative_async(file_path))
        else:
            return self._process_url_file_iterative_multiprocessing(file_path)
    
    def _process_url_file_iterative_multiprocessing(self, file_path: str) -> Dict[str, Any]:
        """Process URLs from a file with iterative subpage discovery using multiprocessing."""
        try:
            self.logger.info(f"Starting iterative knowledge extraction for team: {self.team_id} (Multiprocessing Mode)")
            
            # Load original URLs
            self.original_urls = self._load_urls_from_file(file_path)
            if not self.original_urls:
                self.logger.error("No URLs found in file")
                return self.stats
            
            self.logger.info(f"Loaded {len(self.original_urls)} original URLs from {file_path}")
            
            # Initialize tracking sets
            processed_urls: Set[str] = set()
            current_iteration_urls = self.original_urls.copy()
            
            # Create subpage file path
            subpage_file_path = self._get_subpage_file_path(file_path)
            
            # Initialize subpage file with empty set to ensure it's created
            self._save_urls_to_file(subpage_file_path, set())
            self.logger.info(f"Initialized subpage file: {subpage_file_path}")
            
            iteration = 0
            while current_iteration_urls:
                iteration += 1
                self.stats['iterations_completed'] = iteration
                
                self.logger.info(f"ITERATION {iteration}: Processing {len(current_iteration_urls)} URLs")
                
                # Process current iteration URLs using multiprocessing
                new_discovered_urls = self._process_urls_iteration_parallel(
                    list(current_iteration_urls), processed_urls
                )
                
                self.logger.info(f"ITERATION {iteration}: Discovered {len(new_discovered_urls)} new URLs")
                
                # Update tracking
                processed_urls.update(current_iteration_urls)
                self.all_discovered_urls.update(new_discovered_urls)
                
                # Save discovered URLs to subpage file (always update with cumulative list)
                self._save_urls_to_file(subpage_file_path, self.all_discovered_urls)
                if new_discovered_urls:
                    self.stats['total_new_links_found'] += len(new_discovered_urls)
                
                # Find new URLs that weren't in original file
                new_urls_for_next_iteration = new_discovered_urls - self.original_urls - processed_urls
                
                if new_urls_for_next_iteration:
                    self.logger.info(f"ITERATION {iteration}: Found {len(new_urls_for_next_iteration)} new URLs for next iteration")
                    
                    # Append new URLs to original file
                    appended_count = self._append_urls_to_file(file_path, new_urls_for_next_iteration)
                    self.logger.info(f"ITERATION {iteration}: Appended {appended_count} URLs to main file")
                    
                    # Remove the newly added URLs from subpage file to keep it clean
                    original_urls_before_update = self.original_urls.copy()
                    self._remove_urls_from_subpage_file(subpage_file_path, original_urls_before_update)

                    # Update original URLs set
                    self.original_urls.update(new_urls_for_next_iteration)
                    
                    
                    # Set URLs for next iteration
                    current_iteration_urls = new_urls_for_next_iteration
                else:
                    self.logger.info(f"ITERATION {iteration}: No new URLs found. Stopping.")
                    current_iteration_urls = set()
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info("COMPLETED")
            self.logger.info(f"Total iterations: {iteration}")
            self.logger.info(f"Total URLs processed: {len(processed_urls)}")
            self.logger.info(f"Total subpages discovered: {len(self.all_discovered_urls)}")
            self.logger.info(f"Subpage file: {os.path.basename(subpage_file_path)}")
            self.logger.info(f"{'='*60}")
            
            # Delete subpage file after processing is complete
            self._delete_subpage_file(subpage_file_path)
            
            return self.stats
            
        except Exception as e:
            self.logger.error(f"Error in iterative processing: {e}")
            self.stats['errors'].append(str(e))
            # Clean up subpage file even if there's an error
            if 'subpage_file_path' in locals():
                self._delete_subpage_file(subpage_file_path)
            return self.stats
    
    async def _process_url_file_iterative_async(self, file_path: str) -> Dict[str, Any]:
        """Process URLs from a file with iterative subpage discovery using async."""
        try:
            self.logger.info(f"Starting iterative knowledge extraction for team: {self.team_id} (Async Mode)")
            
            # Load original URLs
            self.original_urls = self._load_urls_from_file(file_path)
            if not self.original_urls:
                self.logger.error("No URLs found in file")
                return self.stats
            
            self.logger.info(f"Loaded {len(self.original_urls)} original URLs from {file_path}")
            
            # Initialize tracking sets
            processed_urls: Set[str] = set()
            current_iteration_urls = self.original_urls.copy()
            
            # Create subpage file path
            subpage_file_path = self._get_subpage_file_path(file_path)
            
            # Initialize subpage file with empty set to ensure it's created
            self._save_urls_to_file(subpage_file_path, set())
            self.logger.info(f"Initialized subpage file: {subpage_file_path}")
            
            iteration = 0
            while current_iteration_urls:
                iteration += 1
                self.stats['iterations_completed'] = iteration
                
                self.logger.info(f"ITERATION {iteration}: Processing {len(current_iteration_urls)} URLs")
                
                # Process current iteration URLs using async
                new_discovered_urls = await self._process_urls_iteration_async(
                    list(current_iteration_urls), processed_urls
                )
                
                self.logger.info(f"ITERATION {iteration}: Discovered {len(new_discovered_urls)} new URLs")
                
                # Update tracking
                processed_urls.update(current_iteration_urls)
                self.all_discovered_urls.update(new_discovered_urls)
                
                # Save discovered URLs to subpage file (always update with cumulative list)
                self._save_urls_to_file(subpage_file_path, self.all_discovered_urls)
                if new_discovered_urls:
                    self.stats['total_new_links_found'] += len(new_discovered_urls)
                
                # Find new URLs that weren't in original file
                new_urls_for_next_iteration = new_discovered_urls - self.original_urls - processed_urls
                
                if new_urls_for_next_iteration:
                    self.logger.info(f"ITERATION {iteration}: Found {len(new_urls_for_next_iteration)} new URLs for next iteration")
                    
                    # Append new URLs to original file
                    appended_count = self._append_urls_to_file(file_path, new_urls_for_next_iteration)
                    self.logger.info(f"ITERATION {iteration}: Appended {appended_count} URLs to main file")
                    
                    # Remove the newly added URLs from subpage file to keep it clean
                    original_urls_before_update = self.original_urls.copy()
                    self._remove_urls_from_subpage_file(subpage_file_path, original_urls_before_update)

                    # Update original URLs set
                    self.original_urls.update(new_urls_for_next_iteration)
                    
                    # Set URLs for next iteration
                    current_iteration_urls = new_urls_for_next_iteration
                else:
                    self.logger.info(f"ITERATION {iteration}: No new URLs found. Stopping.")
                    current_iteration_urls = set()
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info("COMPLETED")
            self.logger.info(f"Total iterations: {iteration}")
            self.logger.info(f"Total URLs processed: {len(processed_urls)}")
            self.logger.info(f"Total subpages discovered: {len(self.all_discovered_urls)}")
            self.logger.info(f"Subpage file: {os.path.basename(subpage_file_path)}")
            self.logger.info(f"{'='*60}")
            
            # Delete subpage file after processing is complete
            self._delete_subpage_file(subpage_file_path)
            
            return self.stats
            
        except Exception as e:
            self.logger.error(f"Error in iterative processing: {e}")
            self.stats['errors'].append(str(e))
            # Clean up subpage file even if there's an error
            if 'subpage_file_path' in locals():
                self._delete_subpage_file(subpage_file_path)
            return self.stats
    
    def _process_urls_iteration_parallel(self, urls: list, processed_urls: set) -> set:
        if not self.process_pool:
            raise RuntimeError("Process pool not initialized")
        iteration_discovered_urls = set()
        
        # Submit all URLs to process pool
        futures = []
        for url in urls:
            future = self.process_pool.apply_async(
                process_single_url_worker,
                args=(url, self.team_id, self.user_id, self.skip_existing_urls)
            )
            futures.append((future, url))
        
        # Collect results as they complete (non-blocking parallel collection)
        for future, url in futures:
            try:
                result = future.get()  # type: ignore[attr-defined]
                if result:
                    if result.get('skipped'):
                        self.stats['urls_skipped'] += 1
                        self.logger.info(f"SKIP: {url}")
                    else:
                        self.stats['urls_processed'] += 1
                        if result.get('subpages'):
                            iteration_discovered_urls.update(result['subpages'])
                            self.stats['subpages_discovered'] += len(result['subpages'])
                            self.logger.info(f"URL: {url} -> {len(result['subpages'])} subpages")
                        if result.get('content_extracted'):
                            self.stats['content_extracted'] += 1
                        if result.get('knowledge_saved'):
                            self.stats['knowledge_items_saved'] += 1
                        if result.get('error'):
                            self.stats['urls_failed'] += 1
                            self.stats['errors'].append(f"Error processing {url}: {result['error']}")
                            self.logger.info(f"ERROR: {url} - {result['error']}")
                else:
                    self.stats['urls_failed'] += 1
                    self.logger.info(f"FAILED: {url}")
            except Exception as e:
                self.stats['urls_failed'] += 1
                self.stats['errors'].append(f"Error processing {url}: {str(e)}")
                self.logger.info(f"EXCEPTION: {url} - {str(e)}")
        
        new_discovered = iteration_discovered_urls - processed_urls - set(urls)
        return new_discovered
    
    async def _process_urls_iteration_async(self, urls: List[str], processed_urls: Set[str]) -> Set[str]:
        """Process a set of URLs in one iteration using async and return newly discovered URLs."""
        if not self.url_processor:
            raise RuntimeError("URL processor not initialized for async mode")
        
        # Track discovered URLs for this iteration
        iteration_discovered_urls = set()
        
        # Process URLs in parallel with controlled concurrency
        semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_REQUESTS)
        tasks = []
        
        for url in urls:
            task = asyncio.create_task(self._process_single_url_async(url, semaphore, iteration_discovered_urls))
            tasks.append(task)
        
        # Wait for all tasks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Return newly discovered URLs (excluding already processed ones)
        new_discovered = iteration_discovered_urls - processed_urls - set(urls)
        
        return new_discovered
    
    async def _process_single_url_async(self, url: str, semaphore: asyncio.Semaphore, iteration_discovered_urls: Set[str]):
        """Process a single URL in async mode."""
        async with semaphore:
            try:
                # Check if URL should be skipped (already exists in database)
                if self._should_skip_url(url):
                    self.stats['urls_skipped'] += 1
                    self.logger.info(f"Skipping URL (already in database): {url}")
                    return
                
                self.logger.info(f"Processing URL: {url}")
                
                # Step 1: Discover subpages
                if self.url_processor:
                    subpages = await self.url_processor.discover_subpages(url)
                    if subpages:
                        # Add discovered URLs to our tracking set
                        iteration_discovered_urls.update(subpages)
                        self.stats['subpages_discovered'] += len(subpages)
                        self.logger.info(f"Discovered {len(subpages)} subpages from {url}")
                
                # Step 2: Extract content
                if self.content_extractor:
                    content_data = await self.content_extractor.extract_content(url)
                    if not content_data:
                        self.stats['urls_failed'] += 1
                        self.logger.warning(f"Failed to extract content from {url}")
                        return
                    
                    self.stats['content_extracted'] += 1
                    
                    # Step 3: Validate content with LLM
                    if self.llm_processor:
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
                        if self.db_handler:
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
    
    def process_url_file(self, file_path: str, save_discovered_urls: bool = True) -> Dict[str, Any]:
        """Process URLs from a file and extract knowledge using selected processing mode."""
        if self.processing_mode == "async":
            import asyncio
            return asyncio.run(self._process_url_file_async(file_path, save_discovered_urls))
        else:
            return self._process_url_file_multiprocessing(file_path, save_discovered_urls)
    
    def _process_url_file_multiprocessing(self, file_path: str, save_discovered_urls: bool = True) -> Dict[str, Any]:
        """Process URLs from a file and extract knowledge using multiprocessing."""
        try:
            self.logger.info(f"Starting knowledge extraction for team: {self.team_id} (Multiprocessing Mode)")
            
            # Load URLs from file
            urls = self._load_urls_from_file(file_path)
            if not urls:
                self.logger.error("No URLs found in file")
                return self.stats
            
            self.logger.info(f"Loaded {len(urls)} URLs from {file_path}")
            
            # Process URLs using multiprocessing
            self._process_urls_parallel(list(urls))
            
            # Save discovered URLs back to file if requested
            if save_discovered_urls:
                all_urls = self.original_urls | self.all_discovered_urls
                self._save_urls_to_file(file_path, all_urls)
                self.logger.info(f"Saved {len(all_urls)} URLs back to {file_path}")
            
            self.logger.info("Knowledge extraction completed")
            return self.stats
            
        except Exception as e:
            self.logger.error(f"Error processing URL file: {e}")
            self.stats['errors'].append(str(e))
            return self.stats
    
    async def _process_url_file_async(self, file_path: str, save_discovered_urls: bool = True) -> Dict[str, Any]:
        """Process URLs from a file and extract knowledge using async."""
        try:
            self.logger.info(f"Starting knowledge extraction for team: {self.team_id} (Async Mode)")
            
            # Load URLs from file
            urls = self._load_urls_from_file(file_path)
            if not urls:
                self.logger.error("No URLs found in file")
                return self.stats
            
            self.logger.info(f"Loaded {len(urls)} URLs from {file_path}")
            
            # Process URLs using async
            await self._process_urls_async(list(urls))
            
            # Save discovered URLs back to file if requested
            if save_discovered_urls:
                all_urls = self.original_urls | self.all_discovered_urls
                self._save_urls_to_file(file_path, all_urls)
                self.logger.info(f"Saved {len(all_urls)} URLs back to {file_path}")
            
            self.logger.info("Knowledge extraction completed")
            return self.stats
            
        except Exception as e:
            self.logger.error(f"Error processing URL file: {e}")
            self.stats['errors'].append(str(e))
            return self.stats
    
    async def _process_urls_async(self, urls: List[str]):
        """Process URLs in parallel using async."""
        if not self.url_processor:
            raise RuntimeError("URL processor not initialized for async mode")
        
        # Process URLs in parallel with controlled concurrency
        semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_REQUESTS)
        
        tasks = []
        for url in urls:
            task = asyncio.create_task(self._process_single_url_async(url, semaphore, set()))
            tasks.append(task)
        
        # Wait for all tasks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_team_knowledge(self) -> Dict[str, Any] | None:
        """Retrieve all knowledge for the team."""
        try:
            # Create a temporary database handler for this process
            temp_handler = DatabaseHandler()
            
            # Create a new event loop for this thread/process
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            try:
                # Connect and get team data
                loop.run_until_complete(temp_handler.connect())
                team_data = loop.run_until_complete(temp_handler.get_team_knowledge(self.team_id))
                
                # Clean up connection
                loop.run_until_complete(temp_handler.disconnect())
                
                return team_data
                
            finally:
                if loop.is_running():
                    loop.close()
                    
        except Exception as e:
            self.logger.error(f"Error retrieving team knowledge: {e}")
        return None
    
    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Search knowledge within the team."""
        try:
            # Create a temporary database handler for this process
            temp_handler = DatabaseHandler()
            
            # Create a new event loop for this thread/process
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            try:
                # Connect and search
                loop.run_until_complete(temp_handler.connect())
                search_results = loop.run_until_complete(temp_handler.search_knowledge(self.team_id, query))
                
                # Clean up connection
                loop.run_until_complete(temp_handler.disconnect())
                
                return search_results
                
            finally:
                if loop.is_running():
                    loop.close()
                    
        except Exception as e:
            self.logger.error(f"Error searching knowledge: {e}")
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.copy()

    def _process_urls_parallel(self, urls: List[str]):
        """Process URLs in parallel using multiprocessing."""
        if not self.process_pool:
            raise RuntimeError("Process pool not initialized")
        
        # Submit all URLs to process pool
        future_to_url = {}
        for url in urls:
            future = self.process_pool.apply_async(
                process_single_url_worker,
                args=(url, self.team_id, self.user_id, self.skip_existing_urls)
            )
            future_to_url[future] = url
        
        # Collect results as they complete
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                if result:
                    # Update statistics
                    if result.get('skipped'):
                        self.stats['urls_skipped'] += 1
                        self.logger.info(f"SKIP: {url}")
                    else:
                        self.stats['urls_processed'] += 1
                        if result.get('subpages'):
                            self.all_discovered_urls.update(result['subpages'])
                            self.stats['subpages_discovered'] += len(result['subpages'])
                        if result.get('content_extracted'):
                            self.stats['content_extracted'] += 1
                        if result.get('knowledge_saved'):
                            self.stats['knowledge_items_saved'] += 1
                        if result.get('error'):
                            self.stats['urls_failed'] += 1
                            self.stats['errors'].append(f"Error processing {url}: {result['error']}")
                            self.logger.info(f"ERROR: {url} - {result['error']}")
                else:
                    self.stats['urls_failed'] += 1
                    self.logger.info(f"FAILED: {url}")
            except Exception as e:
                self.stats['urls_failed'] += 1
                self.stats['errors'].append(f"Error processing {url}: {str(e)}")
                self.logger.info(f"EXCEPTION: {url} - {str(e)}")

def process_single_url_worker(url: str, team_id: str, user_id: str, skip_existing_urls: bool = False) -> Dict[str, Any]:
    """Worker function to process a single URL in a separate process."""
    try:
        # Initialize components for this process
        url_processor = URLProcessor()
        content_extractor = ContentExtractor()
        llm_processor = LLMProcessor()
        db_handler = DatabaseHandler()
        
        result = {
            'url': url,
            'subpages': [],
            'content_extracted': False,
            'knowledge_saved': False,
            'skipped': False,
            'error': None
        }
        
        # Check if URL should be skipped (already exists in database)
        if skip_existing_urls:
            try:
                # Create a new event loop for this thread/process
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                try:
                    # Connect using shared connection pool
                    loop.run_until_complete(db_handler.connect())
                    team_data = loop.run_until_complete(db_handler.get_team_knowledge(team_id))
                    
                    if team_data and 'items' in team_data:
                        existing_urls = {item.get('source_url', '') for item in team_data['items'] if item.get('source_url')}
                        if url in existing_urls:
                            result['skipped'] = True
                            result['error'] = "URL already exists in database"
                            # Don't disconnect since we're using shared pool
                            return result
                    
                    # Don't disconnect since we're using shared pool
                    
                finally:
                    if loop.is_running():
                        loop.close()
                        
            except Exception as e:
                # If we can't check the database, continue processing
                pass
        
        # Step 1: Discover subpages
        subpages = url_processor.discover_subpages_sync(url)
        if subpages:
            result['subpages'] = subpages
        
        # Step 2: Extract content
        content_data = content_extractor.extract_content_sync(url)
        if not content_data:
            result['error'] = "Failed to extract content"
            return result
        
        result['content_extracted'] = True
        
        # Step 3: Validate content with LLM
        is_valid = llm_processor.validate_content_sync(content_data)
        if not is_valid:
            result['error'] = "Content not suitable for knowledge extraction"
            return result
        
        # Step 4: Process content with LLM
        knowledge_data = llm_processor.process_content_sync(
            content_data, team_id, user_id
        )
        if not knowledge_data:
            result['error'] = "Failed to process content with LLM"
            return result
        
        # Step 5: Save to database using shared connection pool
        success = db_handler.save_knowledge_item_sync(knowledge_data)
        if success:
            result['knowledge_saved'] = True
        else:
            result['error'] = "Failed to save knowledge item"
        
        return result
        
    except Exception as e:
        return {
            'url': url,
            'subpages': [],
            'content_extracted': False,
            'knowledge_saved': False,
            'skipped': False,
            'error': str(e)
        }

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Knowledge Scraper for Technical Content')
    parser.add_argument('url_file', help='Path to file containing URLs (one per line)')
    parser.add_argument('--team-id', required=True, help='Team ID for organizing knowledge')
    parser.add_argument('--user-id', default='', help='User ID (optional)')
    parser.add_argument('--save-urls', action='store_true', help='Save discovered URLs back to file')
    parser.add_argument('--iterative', action='store_true', help='Use iterative subpage discovery')
    parser.add_argument('--processing-mode', choices=['multiprocessing', 'async'], default='multiprocessing', 
                       help='Processing mode: multiprocessing (default) or async')
    parser.add_argument('--skip-existing', action='store_true', help='Skip URLs that already exist in database')
    parser.add_argument('--search', help='Search existing knowledge')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    
    args = parser.parse_args()
    
    if args.processing_mode == "multiprocessing":
        listener, log_queue = setup_logging_queue()
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        listener = None
        log_queue = None
    logger = logging.getLogger(__name__)
    
    try:
        if args.processing_mode == "async":
            async def run_async():
                async with KnowledgeScraper(args.team_id, args.user_id, args.processing_mode, args.skip_existing, log_queue=log_queue) as scraper:
                    if args.search:
                        # Search existing knowledge
                        results = scraper.search_knowledge(args.search)
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
                        stats = scraper.get_statistics()
                        print("\nDatabase Statistics:")
                        for key, value in stats.items():
                            print(f"  {key}: {value}")
                    
                    else:
                        # Process URLs
                        if not os.path.exists(args.url_file):
                            logger.error(f"URL file not found: {args.url_file}")
                            return
                        
                        if args.iterative:
                            # Use iterative processing
                            stats = await scraper._process_url_file_iterative_async(args.url_file)
                        else:
                            # Use legacy processing
                            stats = await scraper._process_url_file_async(args.url_file, args.save_urls)
                        
                        print("\nProcessing Statistics:")
                        for key, value in stats.items():
                            if key != 'errors':
                                print(f"  {key}: {value}")
                        
                        if stats['errors']:
                            print("\nErrors:")
                            for error in stats['errors']:
                                print(f"  - {error}")
            
            # Run async function
            asyncio.run(run_async())
            
        else:
            with KnowledgeScraper(args.team_id, args.user_id, args.processing_mode, args.skip_existing, log_queue=log_queue) as scraper:
                if args.search:
                    # Search existing knowledge
                    results = scraper.search_knowledge(args.search)
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
                    stats = scraper.get_statistics()
                    print("\nDatabase Statistics:")
                    for key, value in stats.items():
                        print(f"  {key}: {value}")
                
                else:
                    # Process URLs
                    if not os.path.exists(args.url_file):
                        logger.error(f"URL file not found: {args.url_file}")
                        return
                    
                    if args.iterative:
                        # Use iterative processing
                        stats = scraper.process_url_file_iterative(args.url_file)
                    else:
                        # Use legacy processing
                        stats = scraper.process_url_file(args.url_file, args.save_urls)
                    
                    print("\nProcessing Statistics:")
                    for key, value in stats.items():
                        if key != 'errors':
                            print(f"  {key}: {value}")
                    
                    if stats['errors']:
                        print("\nErrors:")
                        for error in stats['errors']:
                            print(f"  - {error}")
    finally:
        if listener:
            listener.stop()

if __name__ == "__main__":
    main() 