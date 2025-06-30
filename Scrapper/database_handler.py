import logging
from typing import Dict, Any, List, Optional
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
import json
from datetime import datetime, timezone
import asyncio
import threading

from config import Config

class DatabaseHandler:
    _connection_pool = None
    _pool_lock = threading.Lock()
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collection = None
        
    @classmethod
    def get_connection_pool(cls):
        """Get or create a shared MongoDB connection pool."""
        if cls._connection_pool is None:
            with cls._pool_lock:
                if cls._connection_pool is None:
                    cls._connection_pool = MongoClient(
                        Config.MONGODB_URI,
                        maxPoolSize=50,  # Allow more concurrent connections
                        minPoolSize=10,  # Keep minimum connections ready
                        maxIdleTimeMS=30000,  # Close idle connections after 30 seconds
                        waitQueueTimeoutMS=5000,  # Wait up to 5 seconds for available connection
                        retryWrites=True,
                        retryReads=True
                    )
                    cls.logger = logging.getLogger(__name__)
                    cls.logger.info("Created MongoDB connection pool with maxPoolSize=50, minPoolSize=10")
        return cls._connection_pool
    
    @classmethod
    def close_connection_pool(cls):
        """Close the shared connection pool."""
        if cls._connection_pool is not None:
            with cls._pool_lock:
                if cls._connection_pool is not None:
                    cls._connection_pool.close()
                    cls._connection_pool = None
                    cls.logger.info("Closed MongoDB connection pool")
        
    async def connect(self):
        """Connect to MongoDB Atlas using connection pool."""
        try:
            # Use the shared connection pool
            self.client = self.get_connection_pool()
            
            # Test the connection
            self.client.admin.command('ping')
            
            self.db = self.client[Config.MONGODB_DATABASE]
            self.collection = self.db[Config.MONGODB_COLLECTION]
            
            # Create indexes for better performance
            self.collection.create_index([("team_id", 1)])
            self.collection.create_index([("items.source_url", 1)])
            self.collection.create_index([("items.title", 1)])
            
            self.logger.info(f"Connected to MongoDB: {Config.MONGODB_DATABASE}.{Config.MONGODB_COLLECTION}")
            
        except ConnectionFailure as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error connecting to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB (doesn't close shared connection pool)."""
        # Don't close the client since it's a shared connection pool
        # The connection pool will be managed separately
        self.client = None
        self.db = None
        self.collection = None
        self.logger.info("Disconnected from MongoDB (connection pool remains active)")
    
    async def save_knowledge_item(self, knowledge_data: Dict[str, Any]) -> bool:
        """Save a knowledge item to the database."""
        try:
            if self.collection is None:
                raise Exception("Database not connected")
            
            team_id = knowledge_data.get('team_id')
            items = knowledge_data.get('items', [])
            
            if not team_id or not items:
                self.logger.warning("Invalid knowledge data: missing team_id or items")
                return False
            
            # Check if team document exists
            existing_team = self.collection.find_one({"team_id": team_id})
            
            if existing_team:
                # Update existing team document by adding new items
                for item in items:
                    # Check if item already exists (by source_url)
                    source_url = item.get('source_url', '')
                    if source_url:
                        existing_item = self.collection.find_one({
                            "team_id": team_id,
                            "items.source_url": source_url
                        })
                        
                        if existing_item:
                            self.logger.info(f"Item already exists for URL: {source_url}")
                            continue
                    
                    # Add timestamp to item
                    item['created_at'] = datetime.now(timezone.utc)
                    item['updated_at'] = datetime.now(timezone.utc)
                    
                    # Add item to existing team
                    result = self.collection.update_one(
                        {"team_id": team_id},
                        {"$push": {"items": item}}
                    )
                    
                    if result.modified_count > 0:
                        self.logger.info(f"Added item to team {team_id}: {item.get('title', 'Unknown')}")
                    else:
                        self.logger.warning(f"Failed to add item to team {team_id}")
                        
            else:
                # Create new team document
                for item in items:
                    item['created_at'] = datetime.now(timezone.utc)
                    item['updated_at'] = datetime.now(timezone.utc)
                
                team_document = {
                    "team_id": team_id,
                    "items": items,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
                
                result = self.collection.insert_one(team_document)
                
                if result.inserted_id:
                    self.logger.info(f"Created new team document for {team_id} with {len(items)} items")
                else:
                    self.logger.warning(f"Failed to create team document for {team_id}")
            
            return True
            
        except DuplicateKeyError as e:
            self.logger.error(f"Duplicate key error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error saving knowledge item: {e}")
            return False
    
    def save_knowledge_item_sync(self, knowledge_data: Dict[str, Any]) -> bool:
        """Synchronous version of save_knowledge_item for multiprocessing workers."""
        import asyncio
        
        # Create a new event loop for this thread/process
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            # Create a new database handler and connect using shared pool
            temp_handler = DatabaseHandler()
            loop.run_until_complete(temp_handler.connect())
            
            # Run the save operation
            result = loop.run_until_complete(temp_handler.save_knowledge_item(knowledge_data))
            
            # Don't disconnect since we're using shared pool
            # loop.run_until_complete(temp_handler.disconnect())
            
            return result
        finally:
            if loop.is_running():
                loop.close()
    
    async def get_team_knowledge(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve all knowledge items for a team."""
        try:
            if self.collection is None:
                raise Exception("Database not connected")
            
            team_document = self.collection.find_one({"team_id": team_id})
            return team_document
            
        except Exception as e:
            self.logger.error(f"Error retrieving team knowledge: {e}")
            return None
    
    async def search_knowledge(self, team_id: str, query: str) -> List[Dict[str, Any]]:
        """Search knowledge items within a team."""
        try:
            if self.collection is None:
                raise Exception("Database not connected")
            
            # Create text search index if it doesn't exist
            try:
                self.collection.create_index([("items.content", "text"), ("items.title", "text")])
            except Exception:
                pass  # Index might already exist
            
            # Perform text search
            search_results = self.collection.find({
                "team_id": team_id,
                "$text": {"$search": query}
            })
            
            results = []
            for doc in search_results:
                # Filter items that match the search
                matching_items = []
                for item in doc.get('items', []):
                    if query.lower() in item.get('content', '').lower() or query.lower() in item.get('title', '').lower():
                        matching_items.append(item)
                
                if matching_items:
                    results.append({
                        "team_id": doc.get('team_id'),
                        "items": matching_items
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching knowledge: {e}")
            return []
    
    async def delete_team_knowledge(self, team_id: str) -> bool:
        """Delete all knowledge items for a team."""
        try:
            if self.collection is None:
                raise Exception("Database not connected")
            
            result = self.collection.delete_one({"team_id": team_id})
            
            if result.deleted_count > 0:
                self.logger.info(f"Deleted team knowledge for {team_id}")
                return True
            else:
                self.logger.warning(f"No team found to delete: {team_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting team knowledge: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            if self.collection is None:
                raise Exception("Database not connected")
            
            total_teams = self.collection.count_documents({})
            total_items = self.collection.aggregate([
                {"$unwind": "$items"},
                {"$count": "total"}
            ])
            
            total_items_count = 0
            for doc in total_items:
                total_items_count = doc.get('total', 0)
                break
            
            return {
                "total_teams": total_teams,
                "total_items": total_items_count,
                "database_name": Config.MONGODB_DATABASE,
                "collection_name": Config.MONGODB_COLLECTION
            }
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}
    
    def get_statistics_sync(self) -> Dict[str, Any]:
        """Synchronous version of get_statistics for multiprocessing workers."""
        import asyncio
        
        # Create a new event loop for this thread/process
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            # Create a new database handler and connect using shared pool
            temp_handler = DatabaseHandler()
            loop.run_until_complete(temp_handler.connect())
            
            # Run the statistics operation
            result = loop.run_until_complete(temp_handler.get_statistics())
            
            # Don't disconnect since we're using shared pool
            # loop.run_until_complete(temp_handler.disconnect())
            
            return result
        finally:
            if loop.is_running():
                loop.close() 