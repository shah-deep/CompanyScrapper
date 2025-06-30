#!/bin/bash

echo "🏢 Company Crawler & Scrapper UI"
echo "================================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    echo "Please install Python 3 and try again"
    exit 1
fi

# Check if we're in the right directory structure
if [ ! -f "UI/app.py" ]; then
    echo "❌ UI/app.py not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Make the script executable
chmod +x UI/run_ui.py

# Run the launcher script
python3 UI/run_ui.py 