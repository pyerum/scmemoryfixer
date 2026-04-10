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

try:
    import mutagen
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False
    logging.warning("mutagen not available - video metadata functions disabled")

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
            
            # Add location data if available
            if metadata.get('location'):
                self._add_gps_data(exif_dict, metadata['location'])
            
            # Convert back to bytes and save
            exif_bytes = piexif.dump(exif_dict)
            img.save(image_path, exif=exif_bytes)
            
            # Update file modification time to match the actual date from JSON
            # This is the correct date the picture was taken
            import os
            timestamp = date_obj.timestamp()
            os.utime(image_path, (timestamp, timestamp))
            
            logger.info(f"Updated metadata for {image_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating metadata for {image_path.name}: {e}")
            return False
    
    def update_video_metadata(self, video_path: Path, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a video file (MP4/QuickTime format).
        Sets CreateDate, ModifyDate, MediaCreateDate, MediaModifyDate, and GPSCoordinates.
        """
        if not HAS_MUTAGEN:
            logger.error("mutagen not available - cannot update video metadata")
            return False
        
        date_obj = self.parse_snapchat_date(metadata['date']) if metadata.get('date') else None
        
        if not date_obj:
            logger.warning(f"No valid date for {video_path.name}")
            return False
        
        try:
            # Format date for QuickTime metadata (ISO 8601 format)
            # QuickTime uses format like: "2024-01-15T14:30:00Z"
            date_iso = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Load MP4 file directly
            from mutagen.mp4 import MP4
            video_file = MP4(str(video_path))
            
            # Initialize tags if needed
            if video_file.tags is None:
                video_file.add_tags()
            
            # Update QuickTime date fields
            # CreateDate (©day), ModifyDate (©mod)
            date_fields = [
                '©day',  # CreateDate (QuickTime)
                '©mod',  # ModifyDate (QuickTime)  
            ]
            
            for field in date_fields:
                video_file.tags[field] = [date_iso]
            
            # Also try alternative field names for compatibility
            alt_date_fields = [
                'com.apple.quicktime.creationdate',
                'com.apple.quicktime.modificationdate',
            ]
            
            for field in alt_date_fields:
                try:
                    video_file.tags[field] = [date_iso]
                except:
                    pass
            
            # Add GPS coordinates if available
            if metadata.get('location'):
                coords = self._parse_location_string(metadata['location'])
                if coords:
                    lat, lon = coords
                    # Format for GPSCoordinates: "+69.483986+20.881018/"
                    gps_str = f"{'+' if lat >= 0 else ''}{lat:.6f}{'+' if lon >= 0 else ''}{lon:.6f}/"
                    
                    # Try standard GPS field
                    try:
                        video_file.tags['©xyz'] = [gps_str]  # GPSCoordinates
                    except:
                        pass
                    
                    # Also try alternative GPS field
                    try:
                        video_file.tags['com.apple.quicktime.location.ISO6709'] = [gps_str]
                    except:
                        pass
            
            # Save the metadata
            video_file.save()
            
            # Update file modification time to match the actual date from JSON
            import os
            timestamp = date_obj.timestamp()
            os.utime(video_path, (timestamp, timestamp))
            
            logger.info(f"Updated video metadata for {video_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating video metadata for {video_path.name}: {e}", exc_info=True)
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
    
    def _add_gps_data(self, exif_dict: Dict, location_str: str):
        """Add GPS data to EXIF dictionary from Snapchat location string."""
        if not HAS_IMAGE_LIBS:
            return
        
        coords = self._parse_location_string(location_str)
        if not coords:
            return
        
        lat, lon = coords
        
        # Convert decimal degrees to EXIF GPS format (degrees, minutes, seconds)
        def dec_to_dms(dec):
            degrees = int(dec)
            minutes = int((dec - degrees) * 60)
            seconds = (dec - degrees - minutes/60) * 3600
            return (degrees, 1), (minutes, 1), (int(seconds * 100), 100)
        
        lat_dms = dec_to_dms(abs(lat))
        lon_dms = dec_to_dms(abs(lon))
        
        # Set GPS reference (N/S for latitude, E/W for longitude)
        lat_ref = b'N' if lat >= 0 else b'S'
        lon_ref = b'E' if lon >= 0 else b'W'
        
        # Add GPS data to EXIF dictionary
        exif_dict['GPS'] = {
            piexif.GPSIFD.GPSLatitudeRef: lat_ref,
            piexif.GPSIFD.GPSLatitude: lat_dms,
            piexif.GPSIFD.GPSLongitudeRef: lon_ref,
            piexif.GPSIFD.GPSLongitude: lon_dms,
        }
        
        logger.debug(f"Added GPS data: {lat}, {lon}")
