#!/bin/bash
# Clean script for Snapchat Memory Fixer project

echo "=== Cleaning Snapchat Memory Fixer Project ==="

# Remove Python cache files
echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete
find . -type f -name ".Python" -delete

# Remove build artifacts
echo "Removing build artifacts..."
rm -rf build/ dist/ 2>/dev/null

# Remove egg-info directories
echo "Removing Python package artifacts..."
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null
find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null

# Remove IDE files
echo "Removing IDE files..."
rm -rf .vscode/ .idea/ 2>/dev/null
find . -type f -name "*.swp" -delete
find . -type f -name "*.swo" -delete
find . -type f -name "*~" -delete

# Remove OS files
echo "Removing OS files..."
find . -type f -name ".DS_Store" -delete
find . -type f -name "Thumbs.db" -delete

# Remove project-specific temporary files
echo "Removing project temporary files..."
rm -f debug_metadata_update.py 2>/dev/null
rm -f test_exiftool_integration.py 2>/dev/null
rm -f test_app.py 2>/dev/null
rm -f snapmemoryfixer-linux-portable.tar.gz 2>/dev/null

echo ""
echo "=== Cleanup completed! ==="
echo "Project is now clean and ready for development or building."