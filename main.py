#!/usr/bin/env python3
"""
Snapchat Memory Fixer - Main Application Entry Point
Fixes metadata for Snapchat memories exported as zip files.
"""

import sys
import os
import logging
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from gui import MemoryFixerGUI
from processor import MemoryProcessor

def setup_logging():
    """Setup logging configuration"""
    log_dir = Path.home() / ".snapmemoryfixer"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "snapmemoryfixer.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def main():
    """Main application entry point"""
    logger = setup_logging()
    logger.info("Starting Snapchat Memory Fixer")
    
    try:
        # Create and run the GUI
        app = MemoryFixerGUI()
        app.run()
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1
    
    logger.info("Application finished successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())