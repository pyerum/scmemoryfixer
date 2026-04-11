"""
ExifTool wrapper for Snapchat Memory Fixer.
Provides a unified interface to exiftool command-line tool bundled with the application.
"""

import subprocess
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class ExifToolWrapper:
    """Wrapper for exiftool command-line tool."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, exiftool_path: Optional[Path] = None):
        """Singleton pattern - ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(ExifToolWrapper, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, exiftool_path: Optional[Path] = None):
        """
        Initialize exiftool wrapper.
        
        Args:
            exiftool_path: Path to exiftool executable. If None, tries to find it.
        """
        # Only initialize once
        if ExifToolWrapper._initialized:
            return
            
        self.exiftool_path = self._find_exiftool(exiftool_path)
        if not self.exiftool_path:
            raise RuntimeError("exiftool not found. Please ensure exiftool is available.")
        
        logger.info(f"Using exiftool at: {self.exiftool_path}")
        
        # Test exiftool
        try:
            version = self._get_version()
            logger.info(f"ExifTool version: {version}")
        except Exception as e:
            raise RuntimeError(f"Failed to run exiftool: {e}")
        
        ExifToolWrapper._initialized = True
    
    def _find_exiftool(self, exiftool_path: Optional[Path]) -> Optional[Path]:
        """Find exiftool executable."""
        # Use provided path if given
        if exiftool_path and exiftool_path.exists():
            return exiftool_path
        
        # Check PyInstaller temporary directory first (if running as packaged executable)
        try:
            import sys
            if hasattr(sys, '_MEIPASS'):
                # Running as PyInstaller packaged executable
                meipass_dir = Path(sys._MEIPASS)
                
                import platform
                system = platform.system()
                
                if system == "Windows":
                    # Windows paths in PyInstaller bundle
                    bundled_paths = [
                        meipass_dir / "exiftool" / "exiftool-13.55_64" / "exiftool(-k).exe",
                        meipass_dir / "exiftool" / "exiftool.exe",
                    ]
                else:
                    # Linux/macOS paths in PyInstaller bundle
                    bundled_paths = [
                        meipass_dir / "exiftool" / "Image-ExifTool-13.55" / "exiftool",
                        meipass_dir / "exiftool" / "exiftool",
                    ]
                
                for path in bundled_paths:
                    if path.exists():
                        return path
        except:
            pass
        
        # Check bundled exiftool in project directory (development mode)
        project_dir = Path(__file__).parent.parent
        
        # Platform-specific executable names
        import platform
        system = platform.system()
        
        bundled_paths = []
        
        if system == "Windows":
            # Windows paths
            bundled_paths = [
                project_dir / "exiftool" / "exiftool-13.55_64" / "exiftool(-k).exe",
                project_dir / "exiftool" / "exiftool.exe",
            ]
        else:
            # Linux/macOS paths
            bundled_paths = [
                project_dir / "exiftool" / "Image-ExifTool-13.55" / "exiftool",
                project_dir / "exiftool" / "exiftool",
            ]
        
        for path in bundled_paths:
            if path.exists():
                return path
        
        # Check system exiftool (non-Windows)
        if system != "Windows":
            try:
                result = subprocess.run(["which", "exiftool"], capture_output=True, text=True)
                if result.returncode == 0:
                    return Path(result.stdout.strip())
            except:
                pass
        
        return None
    
    def _get_version(self) -> str:
        """Get exiftool version."""
        result = self._run_exiftool(["-ver"])
        return result.stdout.strip()
    
    def _run_exiftool(self, args: List[str], input_file: Optional[Path] = None) -> subprocess.CompletedProcess:
        """
        Run exiftool with given arguments.
        
        Args:
            args: List of arguments to pass to exiftool
            input_file: Optional input file path
            
        Returns:
            CompletedProcess object
        """
        cmd = [str(self.exiftool_path)] + args
        if input_file:
            cmd.append(str(input_file))
        
        logger.debug(f"Running exiftool command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False  # Don't raise exception on non-zero exit
            )
            
            if result.returncode != 0:
                logger.warning(f"exiftool returned {result.returncode}: {result.stderr}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to run exiftool: {e}")
            raise
    
    def update_metadata(self, file_path: Path, metadata: Dict[str, Any], 
                       date_obj: Optional[datetime] = None) -> bool:
        """
        Update metadata for a file (image or video).
        
        Args:
            file_path: Path to the file
            metadata: Metadata dictionary from JSON
            date_obj: Optional datetime object (parsed from metadata if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False
        
        # date_obj should already be parsed by the caller
        if not date_obj:
            logger.warning(f"No valid date for {file_path.name}")
            return False
        
        # Format date for EXIF/QuickTime
        # QuickTime uses format: "2024:01:15 14:30:00" (no timezone indicator)
        date_str = date_obj.strftime("%Y:%m:%d %H:%M:%S")
        
        # Prepare common arguments for both images and videos
        exif_args = [
            f"-CreateDate={date_str}",
            f"-ModifyDate={date_str}",
            f"-DateTimeOriginal={date_str}",
            f"-DateTimeDigitized={date_str}",
            f"-DateTime={date_str}",
            # Set TimeZoneOffset for UTC (0 hours)
            "-TimeZoneOffset=0",
            "-overwrite_original",  # Don't create backup file
        ]
        
        # Add video-specific tags for MP4/MOV files
        file_ext = file_path.suffix.lower()
        if file_ext in ['.mp4', '.mov', '.m4v', '.avi', '.mkv']:
            exif_args.extend([
                f"-MediaCreateDate={date_str}",
                f"-MediaModifyDate={date_str}",
                f"-TrackCreateDate={date_str}",
                f"-TrackModifyDate={date_str}",
                f"-CreationDate={date_str}",  # QuickTime movie creation date
                f"-ModificationDate={date_str}",  # QuickTime movie modification date
            ])
        
        # Add GPS coordinates if available
        if metadata.get('location'):
            coords = self._parse_location_string(metadata['location'])
            if coords:
                lat, lon = coords
                # Format for GPSCoordinates: "+69.483986+20.881018"
                gps_str = f"{'+' if lat >= 0 else ''}{lat:.6f}{'+' if lon >= 0 else ''}{lon:.6f}"
                exif_args.append(f"-GPSCoordinates={gps_str}")
                
                # Also set standard GPS tags for images
                if file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif']:
                    exif_args.extend([
                        f"-GPSLatitude={abs(lat)}",
                        f"-GPSLatitudeRef={'N' if lat >= 0 else 'S'}",
                        f"-GPSLongitude={abs(lon)}",
                        f"-GPSLongitudeRef={'E' if lon >= 0 else 'W'}",
                    ])
        
        # Run exiftool
        result = self._run_exiftool(exif_args, file_path)
        
        if result.returncode == 0:
            logger.info(f"Updated metadata for {file_path.name}")
            
            # Update file modification time to match the actual date from JSON
            try:
                timestamp = date_obj.timestamp()
                os.utime(file_path, (timestamp, timestamp))
                logger.debug(f"Updated file timestamps for {file_path.name}")
            except Exception as e:
                logger.warning(f"Failed to update file timestamps: {e}")
            
            return True
        else:
            logger.error(f"Failed to update metadata for {file_path.name}: {result.stderr}")
            return False
    
    def _parse_location_string(self, location_str: str) -> Optional[tuple[float, float]]:
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
    
    def read_metadata(self, file_path: Path, tags: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Read metadata from a file.
        
        Args:
            file_path: Path to the file
            tags: List of specific tags to read (None for all)
            
        Returns:
            Dictionary of tag names and values
        """
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return {}
        
        args = ["-s", "-G"]  # Short output with group names
        if tags:
            for tag in tags:
                args.append(f"-{tag}")
        
        result = self._run_exiftool(args, file_path)
        
        if result.returncode != 0:
            logger.error(f"Failed to read metadata from {file_path.name}: {result.stderr}")
            return {}
        
        # Parse output
        metadata = {}
        for line in result.stdout.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()
        
        return metadata
    
    def test_connection(self) -> bool:
        """Test if exiftool is working."""
        try:
            version = self._get_version()
            return bool(version)
        except:
            return False