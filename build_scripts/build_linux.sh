#!/bin/bash
# Build release script for Snapchat Memory Fixer
# Linux build only - for Windows builds, use build_windows.bat on a Windows machine

set -e  # Exit on error

echo "=== Building Snapchat Memory Fixer Release (Linux) ==="
echo "For Windows builds, run build_windows.bat on a Windows machine"
echo ""

# Get version from version.py
VERSION=$(python3 -c "import sys; sys.path.insert(0, 'src'); from version import VERSION; print(VERSION)")
echo "Building version: $VERSION"

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/ 2>/dev/null || true

# Install dependencies if needed
echo "Checking Python dependencies..."
pip install -r requirements.txt > /dev/null 2>&1 || pip install -r requirements.txt

# Build with PyInstaller
echo "Building executable with PyInstaller..."

EXE_NAME="snapmemoryfixer"
EXE_PATH="dist/$EXE_NAME"

pyinstaller \
    --name="snapmemoryfixer" \
    --onefile \
    --windowed \
    --paths=src \
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
echo "Executable created at: $EXE_PATH"
echo ""

echo "Testing the executable..."
echo "Running quick test (will timeout after 5 seconds)..."
timeout 5 ./dist/snapmemoryfixer 2>&1 | head -5 && echo "Test passed!" || echo "Test completed"

echo ""
echo "=== Creating release package ==="

# Create README for Linux
cat > dist/README.txt << EOF
Snapchat Memory Fixer v${VERSION} - Linux Portable Edition
=========================================================

This is a portable executable for fixing Snapchat memories export files.

Usage:
  ./snapmemoryfixer

Features:
  - Fix metadata for Snapchat memories exported as zip files
  - Merge overlays (text, drawings, filters) with media files
  - Update EXIF data with correct dates from JSON metadata
  - Organize files with snapMemory_ prefix

Requirements:
  - Linux system (tested on Ubuntu/Debian)

How to use:
1. Run the application: ./snapmemoryfixer
2. Add your Snapchat export zip files
3. Select output directory
4. Click "Start Processing"

For more information, visit the GitHub repository.

EOF

# Create release archive with versioned name
echo "Creating release archive..."
cd dist

ARCHIVE_NAME="snapmemoryfixer-v${VERSION}-linux-portable.tar.gz"
echo "Creating Linux tar.gz archive: $ARCHIVE_NAME"
tar -czf ../$ARCHIVE_NAME $EXE_NAME README.txt

echo ""
echo "=== Release package created! ==="
echo "Archive: $ARCHIVE_NAME"
echo "Size: $(du -h ../$ARCHIVE_NAME | cut -f1)"
echo ""
echo "To distribute:"
echo "  1. Upload $ARCHIVE_NAME to GitHub Releases"
echo "  2. Users can extract and run: tar -xzf $ARCHIVE_NAME"
echo "  3. Then run: ./snapmemoryfixer"

cd ..

echo ""
echo "Build process completed successfully!"