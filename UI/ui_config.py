#!/usr/bin/env python3
"""
UI Configuration Settings
"""

# Streamlit configuration
STREAMLIT_CONFIG = {
    "server.port": 9501,
    "server.address": "localhost",
    "browser.gatherUsageStats": False,
    "theme.base": "light",
    "theme.primaryColor": "#1f77b4",
    "theme.backgroundColor": "#ffffff",
    "theme.secondaryBackgroundColor": "#f0f2f6",
    "theme.textColor": "#262730"
}

# UI Settings
UI_SETTINGS = {
    "max_file_preview_lines": 1000,
    "default_max_pages": 50,
    "default_processing_mode": "multiprocessing",
    "default_skip_external": True,
    "default_skip_founder_blogs": True,
    "default_skip_founder_search": True,
    "default_skip_existing_urls": True,
    "default_iterative": True,
    "progress_update_interval": 0.1,  # seconds
}

# Validation settings
VALIDATION = {
    "max_url_length": 2048,
    "max_team_id_length": 100,
    "max_user_id_length": 100,
    "max_additional_urls": 100,
    "max_skip_words": 50,
}

# File paths
PATHS = {
    "data_dir": "../data",
    "scrapped_urls_dir": "../data/scrapped_urls",
    "logs_dir": "../logs",
} 