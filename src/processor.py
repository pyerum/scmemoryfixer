"""
Main processing logic for Snapchat Memory Fixer
"""

import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from utils import (
    extract_uuid_from_filename, extract_zip_files, 
    find_json_file, create_output_structure, clean_temp_directory
)
from metadata import MetadataHandler
from overlay import OverlayHandler

logger = logging.getLogger(__name__)

class MemoryProcessor:
    """Main processor class for handling Snapchat memory files."""
    
    def __init__(self):
        self.metadata_handler = MetadataHandler()
        self.overlay_handler = OverlayHandler()
        self.temp_dir = None
        self.output_structure = None
    
    def process_files(self, zip_paths: List[Path], output_dir: Path, merge_overlays: bool) -> Dict[str, Any]:
        """
        Main processing function.
        Returns a dictionary with processing results.
        """
        results = {
            'total_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'errors': [],
            'start_time': datetime.now(),
            'end_time': None
        }
        
        try:
            # Create temporary directory for extraction
            self.temp_dir = Path(tempfile.mkdtemp(prefix="snapmemory_"))
            logger.info(f"Created temp directory: {self.temp_dir}")
            
            # Create output structure
            self.output_structure = create_output_structure(output_dir)
            
            # Extract zip files
            logger.info(f"Extracting {len(zip_paths)} zip files...")
            extracted_files = extract_zip_files(zip_paths, self.temp_dir)
            
            # Find and load JSON metadata
            json_file = find_json_file(self.temp_dir)
            if not json_file:
                error_msg = "Could not find memories_history.json file"
                results['errors'].append(error_msg)
                logger.error(error_msg)
                return results
            
            logger.info(f"Found JSON file: {json_file}")
            if not self.metadata_handler.load_json_metadata(json_file):
                error_msg = "Failed to load metadata from JSON file"
                results['errors'].append(error_msg)
                logger.error(error_msg)
                return results
            
            # Process media files
            media_files = self._collect_media_files(extracted_files)
            results['total_files'] = len(media_files)
            
            logger.info(f"Processing {len(media_files)} media files...")
            
            for i, (rel_path, media_path) in enumerate(media_files.items()):
                try:
                    success = self._process_single_file(
                        media_path, rel_path, merge_overlays, results
                    )
                    
                    if success:
                        results['processed_files'] += 1
                    else:
                        results['failed_files'] += 1
                    
                    # Log progress every 10 files
                    if (i + 1) % 10 == 0 or (i + 1) == len(media_files):
                        logger.info(f"Progress: {i + 1}/{len(media_files)} files processed")
                        
                except Exception as e:
                    error_msg = f"Error processing {media_path.name}: {e}"
                    results['errors'].append(error_msg)
                    results['failed_files'] += 1
                    logger.error(error_msg, exc_info=True)
            
            # Clean up
            self._cleanup()
            
        except Exception as e:
            error_msg = f"Processing error: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg, exc_info=True)
            self._cleanup()
        
        results['end_time'] = datetime.now()
        return results
    
    def _collect_media_files(self, extracted_files: Dict[str, Path]) -> Dict[str, Path]:
        """Collect only media files (images and videos)."""
        media_files = {}
        
        for rel_path, file_path in extracted_files.items():
            # Skip JSON files and overlay files
            if file_path.suffix.lower() == '.json':
                continue
            
            # Skip overlay files (they'll be handled with their main files)
            if '-overlay' in file_path.stem.lower():
                continue
            
            # Only include main media files
            if '-main' in file_path.stem.lower():
                media_files[rel_path] = file_path
        
        return media_files
    
    def _process_single_file(self, media_path: Path, rel_path: str, 
                            merge_overlays: bool, results: Dict[str, Any]) -> bool:
        """Process a single media file."""
        # Check if output structure is initialized
        if not self.output_structure:
            error_msg = "Output structure not initialized"
            results['errors'].append(error_msg)
            logger.error(error_msg)
            return False
        
        # Extract UUID from filename
        uuid = extract_uuid_from_filename(media_path.name)
        if not uuid:
            error_msg = f"Could not extract UUID from filename: {media_path.name}"
            results['errors'].append(error_msg)
            logger.warning(error_msg)
            return False
        
        # Get metadata for this UUID
        metadata = self.metadata_handler.get_metadata_for_uuid(uuid)
        if not metadata:
            error_msg = f"No metadata found for UUID: {uuid} (file: {media_path.name})"
            results['errors'].append(error_msg)
            logger.warning(error_msg)
            return False
        
        # Determine output directory based on file type
        if media_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            output_dir = self.output_structure['images']
        elif media_path.suffix.lower() == '.mp4':
            output_dir = self.output_structure['videos']
        else:
            error_msg = f"Unsupported file type: {media_path.suffix}"
            results['errors'].append(error_msg)
            logger.warning(error_msg)
            return False
        
        # Create new filename with snapMemory_ prefix
        new_filename = f"snapMemory_{media_path.name}"
        temp_output_path = output_dir / new_filename
        
        # Process overlay
        success, processed_path = self.overlay_handler.process_overlay(
            media_path, temp_output_path, merge_overlays
        )
        
        if not success or not processed_path:
            error_msg = f"Failed to process overlay for: {media_path.name}"
            results['errors'].append(error_msg)
            return False
        
        # Update metadata
        if media_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            metadata_success = self.metadata_handler.update_image_metadata(
                processed_path, metadata
            )
        elif media_path.suffix.lower() == '.mp4':
            metadata_success = self.metadata_handler.update_video_metadata(
                processed_path, metadata
            )
        else:
            metadata_success = False
        
        if not metadata_success:
            logger.warning(f"Could not update metadata for: {media_path.name}")
            # Continue anyway - the file was still processed
        
        logger.info(f"Successfully processed: {media_path.name}")
        return True
    
    def _cleanup(self):
        """Clean up temporary resources."""
        if self.temp_dir:
            clean_temp_directory(self.temp_dir)
            self.temp_dir = None
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self._cleanup()