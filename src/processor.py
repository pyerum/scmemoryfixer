"""
Main processing logic for Snapchat Memory Fixer
"""

import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

try:
    from .utils import (
        extract_uuid_from_filename, sort_zips_by_name,
        extract_single_zip, cleanup_zip_extract,
        collect_media_files_from_extract, find_json_file,
        create_output_structure, clean_temp_directory
    )
    from .metadata import MetadataHandler
    from .overlay import OverlayHandler
except ImportError:
    # Fallback for direct execution
    from utils import (
        extract_uuid_from_filename, sort_zips_by_name,
        extract_single_zip, cleanup_zip_extract,
        collect_media_files_from_extract, find_json_file,
        create_output_structure, clean_temp_directory
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
    
    def process_files(self, zip_paths: List[Path], output_dir: Path, 
                     merge_image_overlays: bool, merge_video_overlays: bool,
                     separate_folders: bool = True, 
                     progress_callback = None) -> Dict[str, Any]:
        """
        Main processing function - processes one zip at a time.
        Returns a dictionary with processing results.
        
        Args:
            zip_paths: List of zip file paths
            output_dir: Output directory for processed files
            merge_image_overlays: Whether to merge overlays with images
            merge_video_overlays: Whether to merge overlays with videos
            separate_folders: Whether to separate images and videos into subdirectories
            progress_callback: Optional callback function for progress updates
                              Signature: callback(zip_current, zip_total, media_current, media_total)
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
            self.output_structure = create_output_structure(output_dir, separate_folders)
            
            # Sort zips so the base one (with JSON) comes first
            sorted_zips = sort_zips_by_name(zip_paths)
            logger.info(f"Processing {len(sorted_zips)} zip files...")
            
            # Track total media files across all zips
            total_media_files = 0
            processed_media_files = 0
            failed_media_files = 0
            
            # Process each zip
            for zip_idx, zip_path in enumerate(sorted_zips):
                logger.info(f"Processing zip {zip_idx + 1}/{len(sorted_zips)}: {zip_path.name}")
                
                # Extract this zip
                if not extract_single_zip(zip_path, self.temp_dir):
                    error_msg = f"Failed to extract {zip_path.name}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
                    failed_media_files += 1
                    continue
                
                # Find JSON file (only from first zip)
                json_file = None
                if zip_idx == 0:
                    json_file = find_json_file(self.temp_dir)
                    if not json_file:
                        error_msg = "Could not find memories_history.json file in first zip"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                        cleanup_zip_extract(self.temp_dir, zip_path.stem)
                        continue
                    
                    logger.info(f"Found JSON file: {json_file}")
                    if not self.metadata_handler.load_json_metadata(json_file):
                        error_msg = "Failed to load metadata from JSON file"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                        cleanup_zip_extract(self.temp_dir, zip_path.stem)
                        continue
                
                # Collect media files from this zip
                media_files = collect_media_files_from_extract(self.temp_dir)
                total_media_files += len(media_files)
                
                logger.info(f"Found {len(media_files)} media files in {zip_path.name}")
                
                # Process media files from this zip
                for media_idx, (rel_path, media_path) in enumerate(media_files.items()):
                    try:
                        # Determine which overlay option to use based on file type
                        if media_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                            merge_overlay = merge_image_overlays
                        elif media_path.suffix.lower() == '.mp4':
                            merge_overlay = merge_video_overlays
                        else:
                            merge_overlay = False
                        
                        success = self._process_single_file(
                            media_path, rel_path, merge_overlay, results
                        )
                        
                        if success:
                            processed_media_files += 1
                            results['processed_files'] += 1
                        else:
                            failed_media_files += 1
                            results['failed_files'] += 1
                        
                        # Send progress update
                        if progress_callback:
                            progress_callback(zip_idx + 1, len(sorted_zips), processed_media_files, total_media_files)
                        
                        # Log progress every 10 files
                        if (processed_media_files + 1) % 10 == 0:
                            logger.info(f"Progress: {processed_media_files}/{total_media_files} files processed")
                            
                    except Exception as e:
                        error_msg = f"Error processing {media_path.name}: {e}"
                        results['errors'].append(error_msg)
                        failed_media_files += 1
                        results['failed_files'] += 1
                        logger.error(error_msg, exc_info=True)
                
                # Clean up this zip's extracted files
                cleanup_zip_extract(self.temp_dir, zip_path.stem)
            
            results['total_files'] = total_media_files
            
            # Clean up
            self._cleanup()
            
        except Exception as e:
            error_msg = f"Processing error: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg, exc_info=True)
            self._cleanup()
        
        results['end_time'] = datetime.now()
        return results
    
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