#!/bin/bash
# Build script for Snapchat Memory Fixer Linux executable

set -e  # Exit on error

echo "=== Building Snapchat Memory Fixer for Linux ==="

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/ 2>/dev/null || true

# Install dependencies if needed
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Build with PyInstaller
echo "Building executable with PyInstaller..."
pyinstaller \
    --name="snapmemoryfixer" \
    --onefile \
    --windowed \
    --add-data="exiftool/Image-ExifTool-13.55/exiftool:exiftool/Image-ExifTool-13.55" \
    --add-data="exiftool/Image-ExifTool-13.55/lib:exiftool/Image-ExifTool-13.55/lib" \
    --add-data="exiftool/Image-ExifTool-13.55/html:exiftool/Image-ExifTool-13.55/html" \
    --add-data="exiftool/Image-ExifTool-13.55/t:exiftool/Image-ExifTool-13.55/t" \
    --add-data="exiftool/Image-ExifTool-13.55/arg_files:exiftool/Image-ExifTool-13.55/arg_files" \
    --add-data="exiftool/Image-ExifTool-13.55/config_files:exiftool/Image-ExifTool-13.55/config_files" \
    --add-data="exiftool/Image-ExifTool-13.55/fmt_files:exiftool/Image-ExifTool-13.55/fmt_files" \
    --hidden-import="PIL" \
    --hidden-import="PIL._imaging" \
    --hidden-import="cv2" \
    --hidden-import="dateutil" \
    --hidden-import="dateutil.parser" \
    --hidden-import="dateutil.relativedelta" \
    --hidden-import="dateutil.tz" \
    --hidden-import="tkinter" \
    --hidden-import="tkinter.filedialog" \
    --hidden-import="tkinter.messagebox" \
    --hidden-import="tkinter.scrolledtext" \
    --hidden-import="queue" \
    --hidden-import="threading" \
    --hidden-import="logging" \
    --hidden-import="json" \
    --hidden-import="pathlib" \
    --hidden-import="typing" \
    --hidden-import="datetime" \
    --hidden-import="os" \
    --hidden-import="sys" \
    --hidden-import="subprocess" \
    --clean \
    main.py

echo ""
echo "=== Build completed successfully! ==="
echo "Executable created at: dist/snapmemoryfixer"
echo ""
echo "To test the executable:"
echo "  ./dist/snapmemoryfixer"
echo ""
echo "To create a release package:"
echo "  tar -czf snapmemoryfixer-linux.tar.gz -C dist snapmemoryfixer README.txt LICENSE"
echo ""
echo "Note: You may need to create README.txt and LICENSE files for the release package."