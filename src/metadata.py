"""
Metadata handling for Snapchat Memory Fixer
Handles EXIF data extraction and modification.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging

# Try to import required libraries
try:
    from PIL import Image
    import piexif
    HAS_IMAGE_LIBS = True
except ImportError:
    HAS_IMAGE_LIBS = False
    logging.warning("PIL/piexif not available - image metadata functions disabled")

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
        """
        try:
            # Remove timezone for simplicity
            date_part = date_str.split(' UTC')[0]
            return datetime.strptime(date_part, "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.warning(f"Could not parse date '{date_str}': {e}")
            return None
    
    def update_image_metadata(self, image_path: Path, metadata: Dict[str, Any]) -> bool:
        """
        Update EXIF metadata for an image file.
        Returns True if successful, False otherwise.
        """
        if not HAS_IMAGE_LIBS:
            logger.error("PIL/piexif not available - cannot update image metadata")
            return False
        
        try:
            # Parse date
            date_obj = self.parse_snapchat_date(metadata['date']) if metadata.get('date') else None
            
            if not date_obj:
                logger.warning(f"No valid date for {image_path.name}")
                return False
            
            # Open image and get existing EXIF
            img = Image.open(image_path)
            exif_dict = {}
            
            try:
                exif_dict = piexif.load(img.info.get('exif', b''))
            except:
                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}
            
            # Update DateTimeOriginal (36867)
            date_str = date_obj.strftime("%Y:%m:%d %H:%M:%S")
            exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_str.encode('utf-8')
            exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = date_str.encode('utf-8')
            
            # Update DateTime (306) in 0th IFD
            exif_dict['0th'][piexif.ImageIFD.DateTime] = date_str.encode('utf-8')
            
            # TODO: Add location data if available
            # if metadata.get('location'):
            #     self._add_gps_data(exif_dict, metadata['location'])
            
            # Convert back to bytes and save
            exif_bytes = piexif.dump(exif_dict)
            img.save(image_path, exif=exif_bytes)
            
            logger.info(f"Updated metadata for {image_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating metadata for {image_path.name}: {e}")
            return False
    
    def update_video_metadata(self, video_path: Path, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a video file.
        Note: MP4 metadata modification is complex and may require ffmpeg.
        For now, we'll just log the intended changes.
        """
        date_obj = self.parse_snapchat_date(metadata['date']) if metadata.get('date') else None
        
        if date_obj:
            logger.info(f"Video {video_path.name} should have date: {date_obj}")
            # TODO: Implement actual video metadata update using ffmpeg or similar
            # For now, we'll update file modification time using os.utime
            try:
                import os
                timestamp = date_obj.timestamp()
                os.utime(video_path, (timestamp, timestamp))
                logger.info(f"Updated file timestamps for {video_path.name}")
                return True
            except Exception as e:
                logger.error(f"Error updating video timestamps: {e}")
        
        return False
    
    def _add_gps_data(self, exif_dict: Dict, location_data: Dict[str, Any]):
        """Add GPS data to EXIF dictionary."""
        # This is a placeholder - would need to parse Snapchat location format
        # and convert to EXIF GPS format
        pass