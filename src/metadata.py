"""
Metadata handling for Snapchat Memory Fixer
Handles EXIF data extraction and modification.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging

# Try to import required libraries (only for image overlay operations)
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logging.warning("PIL not available - image overlay functions disabled")

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logging.warning("OpenCV not available - video functions disabled")

logger = logging.getLogger(__name__)

class MetadataHandler:
    """Handles metadata extraction and modification for media files."""
    
    def __init__(self):
        self.metadata_map = {}  # UUID -> metadata dict
    
    def load_json_metadata(self, json_path: Path) -> bool:
        """
        Load metadata from memories_history.json file.
        Returns True if successful, False otherwise.
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Navigate to Saved Media list
            saved_media = data.get('Saved Media', [])
            
            for item in saved_media:
                download_link = item.get('Download Link', '')
                if not download_link:
                    continue
                    
                # Extract UUID from download link
                try:
                    from .utils import extract_uuid_from_url
                except ImportError:
                    from utils import extract_uuid_from_url
                uuid = extract_uuid_from_url(download_link)
                
                if uuid:
                    self.metadata_map[uuid.lower()] = {
                        'date': item.get('Date'),
                        'media_type': item.get('Media Type'),
                        'location': item.get('Location'),
                        'download_link': download_link,
                        'media_url': item.get('Media Download Url')
                    }
            
            logger.info(f"Loaded metadata for {len(self.metadata_map)} items")
            return True
            
        except Exception as e:
            logger.error(f"Error loading JSON metadata: {e}")
            return False
    
    def get_metadata_for_uuid(self, uuid: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a given UUID."""
        return self.metadata_map.get(uuid.lower())
    
    def parse_snapchat_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse Snapchat date string to datetime object.
        Format example: "2024-01-15 14:30:00 UTC"
        Returns timezone-aware datetime in UTC.
        """
        try:
            # Parse as UTC timezone-aware datetime
            from datetime import timezone
            date_part = date_str.split(' UTC')[0]
            naive_dt = datetime.strptime(date_part, "%Y-%m-%d %H:%M:%S")
            # Make it timezone-aware (UTC)
            return naive_dt.replace(tzinfo=timezone.utc)
        except Exception as e:
            logger.warning(f"Could not parse date '{date_str}': {e}")
            return None
    
    def update_image_metadata(self, image_path: Path, metadata: Dict[str, Any]) -> bool:
        """
        Update EXIF metadata for an image file using exiftool.
        Returns True if successful, False otherwise.
        """
        try:
            # Parse date
            date_obj = self.parse_snapchat_date(metadata['date']) if metadata.get('date') else None
            
            if not date_obj:
                logger.warning(f"No valid date for {image_path.name}")
                return False
            
            # Use exiftool wrapper for metadata update
            from exiftool_wrapper import ExifToolWrapper
            wrapper = ExifToolWrapper()
            
            return wrapper.update_metadata(image_path, metadata, date_obj)
            
        except Exception as e:
            logger.error(f"Error updating metadata for {image_path.name}: {e}")
            return False
    
    def update_video_metadata(self, video_path: Path, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a video file (MP4/QuickTime format) using exiftool.
        Sets CreateDate, ModifyDate, MediaCreateDate, MediaModifyDate, TrackCreateDate, TrackModifyDate.
        Also updates file creation and modification timestamps.
        """
        try:
            # Parse date
            date_obj = self.parse_snapchat_date(metadata['date']) if metadata.get('date') else None
            
            if not date_obj:
                logger.warning(f"No valid date for {video_path.name}")
                return False
            
            # Use exiftool wrapper for metadata update
            from exiftool_wrapper import ExifToolWrapper
            wrapper = ExifToolWrapper()
            
            return wrapper.update_metadata(video_path, metadata, date_obj)
            
        except Exception as e:
            logger.error(f"Error updating metadata for {video_path.name}: {e}")
            return False
    
    def _parse_location_string(self, location_str: str) -> Optional[Tuple[float, float]]:
        """
        Parse Snapchat location string.
        Format: "Latitude, Longitude: 69.483986, 20.881018" or "0.0" for no location.
        Returns (latitude, longitude) or None if invalid.
        """
        if not location_str or location_str == "0.0":
            return None
        
        try:
            # Remove "Latitude, Longitude: " prefix if present
            if "Latitude, Longitude: " in location_str:
                coords_str = location_str.replace("Latitude, Longitude: ", "")
            else:
                coords_str = location_str
            
            # Split by comma and clean up
            parts = [p.strip() for p in coords_str.split(',')]
            if len(parts) >= 2:
                lat = float(parts[0])
                lon = float(parts[1])
                
                # Check if coordinates are valid (not 0.0)
                if abs(lat) < 0.001 and abs(lon) < 0.001:
                    return None
                
                return (lat, lon)
            
        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not parse location string '{location_str}': {e}")
        
        return None
