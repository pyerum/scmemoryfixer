# Snapchat Memory Fixer

A Python GUI application to fix metadata for Snapchat memories exported as zip files.

## Problem Statement

When exporting Snapchat memories, they are split into several ~2GB zip files. Each archive contains media files with incorrect metadata:
- File creation time is set to export time (wrong)
- File modification time has the correct date
- EXIF metadata lacks date/location information
- Overlay files (text/drawings) are separate PNG files

The application extracts, processes, and fixes these files.

## Features

- **Drag & Drop Interface**: Easily add Snapchat export zip files
- **Metadata Correction**: Updates EXIF data with correct dates from JSON metadata
- **Overlay Handling**: Optionally merges PNG overlays with media files
- **File Organization**: Outputs organized files with `snapMemory_` prefix
- **Error Handling**: Graceful handling of missing files/corrupted archives
- **Logging**: Detailed log file creation for troubleshooting

## Installation

### Prerequisites
- Python 3.10 or higher
- Linux-based system (tested on Ubuntu/Debian)

### Setup

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Dependencies
- Pillow (image processing and overlay operations)
- opencv-python-headless (video overlay merging)
- python-dateutil (date parsing)
- **ExifTool** (bundled with application - no separate installation needed)

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. In the GUI:
   - **Add Zip Files**: Drag & drop or click "Add Files" to select Snapchat export zip files
   - **Select Output Directory**: Choose where to save processed files
   - **Options**: Check "Merge overlays with media" if you want overlays embedded
   - **Process**: Click "Start Processing" to begin

3. Output:
   - Processed files are saved in the output directory with `snapMemory_` prefix
   - Images go to `output/images/`
   - Videos go to `output/videos/`
   - Logs go to `output/logs/`

## How It Works

1. **Extraction**: All zip files are extracted to a temporary directory
2. **Metadata Loading**: `memories_history.json` is parsed to build UUID→metadata mapping
3. **File Processing**: Each media file is:
   - Matched to its metadata via UUID in filename
   - Overlay merged (if requested)
   - **Metadata Update**: Using bundled ExifTool for both images and videos:
     - Sets correct date/time from JSON metadata
     - Adds TimeZoneOffset tag (0 for UTC)
     - Adds GPS coordinates if available
     - Updates file creation/modification timestamps
   - Renamed with `snapMemory_` prefix
   - Saved to appropriate output directory
4. **Cleanup**: Temporary files are removed, logs are saved

## File Structure

```
scmemoryfixer/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── src/                # Source code
    ├── gui.py          # Tkinter GUI implementation
    ├── processor.py    # Main processing logic
    ├── metadata.py     # EXIF metadata handling
    ├── overlay.py      # Overlay merging functionality
    └── utils.py        # Utility functions
```

## Testing

A sample export file is available in `/exportExample` for testing:
```bash
python main.py
# Add the example zip file: exportExample/mydata~1775490456493.zip
```

## Limitations

- **Video Metadata**: MP4 metadata modification is limited to file timestamps (full metadata update requires ffmpeg)
- **Location Data**: GPS coordinates from JSON are not yet added to EXIF (placeholder implementation)
- **Large Files**: Processing large video files may be memory-intensive

## Future Improvements

- Add ffmpeg integration for complete video metadata support
- Implement GPS coordinate conversion for EXIF
- Add batch processing with resume capability
- Create Linux package (deb/rpm) for easier installation
- Add dark mode theme

## License

This project is provided as-is for personal use.

## Troubleshooting

### Common Issues

1. **"No module named 'PIL'"**: Install Pillow: `pip install Pillow`
2. **"Could not find memories_history.json"**: Ensure you're using the first zip file from the export
3. **"Permission denied"**: Run with appropriate permissions for output directory
4. **Large files slow processing**: The application processes files sequentially to manage memory

### Logs

Check the log file at `~/.snapmemoryfixer/snapmemoryfixer.log` for detailed error information.