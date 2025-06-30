import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MongoDB Configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://username:password@scrappedinfo.mongodb.net/')
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'knowledgebase')
    MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', 'items')
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-lite')
    
    # Web Scraping Configuration
    MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '10'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    USER_AGENT = os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Content Processing
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '100000'))
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '10000'))  # Size of each chunk in characters
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '100'))  # Overlap between chunks to maintain context
    SUPPORTED_CONTENT_TYPES = [
        'text/html',
        'application/pdf',
        'text/plain'
    ]
    
    # File Paths
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
    LOG_FILE = os.getenv('LOG_FILE', 'scrapper.log') 