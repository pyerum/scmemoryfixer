"""
Utility functions for Snapchat Memory Fixer
"""

import re
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

def extract_uuid_from_filename(filename: str) -> Optional[str]:
    """
    Extract UUID from Snapchat memory filename.
    Format: YYYY-MM-DD_UUUUUUUU-UUUU-UUUU-UUUU-UUUUUUUUUUUU-main.jpg
    Returns the UUID part without the date prefix.
    """
    # Try pattern with underscore separator (YYYY-MM-DD_UUID-UUID-UUID-UUID-UUID)
    pattern1 = r'\d{4}-\d{2}-\d{2}_([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
    match = re.search(pattern1, filename, re.IGNORECASE)
    
    if match:
        return match.group(1)
    
    # Try pattern with hyphen separator (YYYY-MM-DD-UUID-UUID-UUID-UUID-UUID)
    pattern2 = r'\d{4}-\d{2}-\d{2}-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
    match = re.search(pattern2, filename, re.IGNORECASE)
    
    return match.group(1) if match else None

def extract_uuid_from_url(url: str) -> Optional[str]:
    """
    Extract UUID from Download Link URL.
    Format: ...&mid=UUUUUUUU-UUUU-UUUU-UUUU-UUUUUUUUUUUU&tid=...
    """
    pattern = r'&mid=([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
    match = re.search(pattern, url, re.IGNORECASE)
    return match.group(1) if match else None

def extract_zip_files(zip_paths: List[Path], extract_dir: Path) -> Dict[str, Path]:
    """
    Extract all zip files to a temporary directory.
    Returns a dictionary mapping file extensions to their paths.
    """
    extracted_files = {}
    
    for zip_path in zip_paths:
        if not zip_path.exists():
            logger.warning(f"Zip file not found: {zip_path}")
            continue
            
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract all files
                zip_ref.extractall(extract_dir)
                logger.info(f"Extracted {zip_path.name}")
                
        except zipfile.BadZipFile:
            logger.error(f"Bad zip file: {zip_path}")
            continue
        except Exception as e:
            logger.error(f"Error extracting {zip_path}: {e}")
            continue
    
    # Collect all extracted files
    for file_path in extract_dir.rglob("*"):
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if ext in ['.jpg', '.jpeg', '.mp4', '.png', '.json']:
                extracted_files[str(file_path.relative_to(extract_dir))] = file_path
    
    return extracted_files

def find_json_file(extract_dir: Path) -> Optional[Path]:
    """Find the memories_history.json file in the extracted directory."""
    json_patterns = [
        "json/memories_history.json",
        "memories_history.json",
        "*/memories_history.json",
        "**/memories_history.json"
    ]
    
    for pattern in json_patterns:
        for json_file in extract_dir.glob(pattern):
            if json_file.exists():
                return json_file
    
    return None

def create_output_structure(output_dir: Path, separate_folders: bool = True) -> Dict[str, Path]:
    """
    Create output directory structure and return paths.
    If separate_folders is True, creates images/ and videos/ subdirectories.
    If False, uses the output_dir directly for all files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if separate_folders:
        # Create subdirectories
        images_dir = output_dir / "images"
        videos_dir = output_dir / "videos"
        
        images_dir.mkdir(exist_ok=True)
        videos_dir.mkdir(exist_ok=True)
        
        return {
            "images": images_dir,
            "videos": videos_dir,
            "root": output_dir
        }
    else:
        # Use output_dir directly for all files
        return {
            "images": output_dir,
            "videos": output_dir,
            "root": output_dir
        }

def clean_temp_directory(temp_dir: Path):
    """Clean up temporary directory."""
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned temp directory: {temp_dir}")
    except Exception as e:
        logger.warning(f"Could not clean temp directory {temp_dir}: {e}")

def get_file_type(filename: str) -> str:
    """Determine file type from extension."""
    ext = Path(filename).suffix.lower()
    if ext in ['.jpg', '.jpeg', '.png']:
        return 'image'
    elif ext == '.mp4':
        return 'video'
    elif ext == '.json':
        return 'json'
    else:
        return 'unknown'