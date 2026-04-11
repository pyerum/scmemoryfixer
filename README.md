# Snapchat Memories Export Fixer

A Python GUI application to fix metadata for Snapchat memories exported as zip files.

## Problem Statement

When exporting Snapchat memories, they are split into several ~2GB zip files. Each archive contains media files with incorrect metadata:
- File creation/modification time is set to export time
- EXIF (for images) and QuickTime (for videos) metadata lacks date/location information
- Overlay files (the text, filters or drawings you can put on top of snaps) are separate PNG files

The application extracts, processes, and fixes these files.

## Features

- **GUI Interface**: Easily add Snapchat export zip files
- **Metadata Correction**: Updates EXIF/QuickTime data with correct dates/location from the JSON file present in the export
- **Overlay Handling**: Optionally merges PNG overlays with media files
- **File Organization**: Outputs organized files with `snapMemory_` prefix
- **Error Handling**: Graceful handling of missing files/corrupted archives
- **Logging**: Detailed log file creation for troubleshooting

## Installation

### Option 1: Portable Linux Executable (Recommended)
For users who don't want to install Python and dependencies:

1. Download the latest release from GitHub Releases
2. Extract the archive:
   ```bash
   tar -xzf snapmemoryfixer-linux-portable.tar.gz
   ```
3. Run the executable:
   ```bash
   ./snapmemoryfixer
   ```

### Option 2: From Source
#### Prerequisites
- Python 3.10 or higher
- Linux-based system (tested on Ubuntu/Debian)

#### Setup and usage

1. Clone or download this repository
2. Run the start script (automatically sets up virtual environment (if not found)), installs missing dependencies and starts the GUI:
   ```bash
   ./run.sh
   ```

3. In the GUI:
   - **Add Zip Files**: Click "Add Files" to select all your Snapchat export zip files
   - **Select Output Directory**: Choose where to save processed files
   - **Options**: Check "Merge overlays with pictures/videos" if you want overlays put back in them (this is the text you can add on top of snaps, filters and drawings, etc.). If you don't select this you will get the original pictures/videos clear of any text/other that you put on them. You can also toggle "Separate pictures and videos in two sub-directories (/videos and /pictures)", the two sub-directories will be created in the output directory you selected.
   - **Process**: Click "Start Processing" to begin

## How It Works

1. **Extraction**: All zip files are extracted to a temporary directory
2. **Metadata Loading**: `memories_history.json` is parsed to build UUID→metadata mapping
3. **File Processing**: Each media file is:
   - Matched to its metadata via UUID in filename
   - Overlay merged (if requested)
   - **Metadata Update**: Using bundled ExifTool for both images and videos:
     - Sets correct date/time from JSON metadata
     - Adds GPS coordinates if available
     - Updates file "modification" timestamps
   - Renamed with `snapMemory_` prefix
   - Saved to appropriate output directory
4. **Cleanup**: Temporary files are removed, logs are saved

## File Structure

```
scmemoryfixer/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── run.sh              # Development startup script
├── clean.sh            # Clean build artifacts script
├── .gitignore          # Git ignore patterns
├── build_scripts/      # Build and packaging scripts
│   ├── build_linux.sh      # Linux build script
│   ├── build_release.sh    # Release build script
│   └── *.spec              # PyInstaller spec files
├── src/                # Source code
│   ├── gui.py          # Tkinter GUI implementation
│   ├── processor.py    # Main processing logic
│   ├── metadata.py     # EXIF metadata handling
│   ├── overlay.py      # Overlay merging functionality
│   ├── utils.py        # Utility functions
│   └── exiftool_wrapper.py # ExifTool wrapper
└── exiftool/           # Bundled ExifTool binaries
    ├── Image-ExifTool-13.55/    # Linux/macOS version
    └── exiftool-13.55_64/       # Windows version
```

## Limitations

- **Large Files**: Processing large video files may be memory-intensive and could take a while, not a problem on most modern hardware

## Future Improvements

- Refine timezone metadata for files that support it (the json contains UTC datetimes)
- Add batch processing with resume capability
- Add dark mode theme (why not?)

## License

This project is provided as-is for personal use. License TBD

## Troubleshooting

### Common Issues

1. **"Could not find memories_history.json"**: Ensure you're using the first zip file from the export
2. **"Permission denied"**: Run with appropriate permissions for output directory
3. **Large files slow processing**: The application processes files sequentially to manage memory

### Logs

Check the log file at `~/.snapmemoryfixer/snapmemoryfixer.log` for detailed error information.

### Credits

This project uses the following libraries:
- Pillow  # For image overlay operations
- opencv-python-headless  # For video processing
- python-dateutil  # For date parsing
plus, most metadata processing happens thanks to ExifTool binaries directly included in the project for ease of use:
- ExifTool

### Disclaimer
This project is not affiliated in any way with Snapchat or Snap Inc. Snapchat and the Snapchat logo are trademarks of Snapchat Inc.
