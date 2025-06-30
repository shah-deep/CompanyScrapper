#!/usr/bin/env python3
"""
Launcher script for the Company Crawler & Scrapper UI
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Launch the Streamlit UI application"""
    
    # Get the script directory (UI directory)
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    
    print("🏢 Company Crawler & Scrapper UI")
    print("=" * 50)
    
    # Check if we're in the right directory structure
    if not (script_dir / "app.py").exists():
        print("❌ Error: app.py not found in UI directory")
        print(f"   UI directory: {script_dir}")
        print("   Please ensure the UI directory contains app.py")
        sys.exit(1)
    
    # Check if requirements are installed
    print("📦 Checking dependencies...")
    try:
        import streamlit
        import pandas
        import plotly
        print("✅ All dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📥 Installing dependencies...")
        
        try:
            # Change to UI directory for pip install
            os.chdir(script_dir)
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ])
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            print("   Please run: pip install -r UI/requirements.txt")
            sys.exit(1)
    
    # Add project root to Python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    print("🚀 Starting Streamlit application...")
    print("   The UI will open in your default browser")
    print("   If it doesn't open automatically, go to: http://localhost:9501")
    print("   Press Ctrl+C to stop the application")
    print("-" * 50)
    
    # Change to UI directory and run the Streamlit app
    try:
        os.chdir(script_dir)
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "9501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 