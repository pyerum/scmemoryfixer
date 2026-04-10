"""
Overlay handling for Snapchat Memory Fixer
Handles merging PNG overlays onto images and videos.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

# Try to import required libraries
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logging.warning("PIL not available - overlay functions disabled")

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logging.warning("OpenCV not available - video overlay functions disabled")

logger = logging.getLogger(__name__)

class OverlayHandler:
    """Handles overlay merging operations."""
    
    def __init__(self):
        self.overlay_cache = {}
    
    def find_overlay_for_media(self, media_path: Path) -> Optional[Path]:
        """
        Find overlay file for a given media file.
        Overlay files have the same name but end with -overlay.png
        """
        stem = media_path.stem
        if stem.endswith('-main'):
            base_name = stem[:-5]  # Remove '-main'
            overlay_name = f"{base_name}-overlay.png"
            
            # Check in same directory
            overlay_path = media_path.parent / overlay_name
            if overlay_path.exists():
                return overlay_path
            
            # Check in parent directory
            overlay_path = media_path.parent.parent / overlay_name
            if overlay_path.exists():
                return overlay_path
        
        return None
    
    def merge_image_overlay(self, image_path: Path, overlay_path: Path, output_path: Path) -> bool:
        """
        Merge PNG overlay onto JPEG image.
        Returns True if successful, False otherwise.
        """
        if not HAS_PIL:
            logger.error("PIL not available - cannot merge image overlays")
            return False
        
        try:
            # Get original timestamps to preserve them
            import os
            orig_atime = os.path.getatime(image_path)
            orig_mtime = os.path.getmtime(image_path)
            
            # Open base image and overlay
            base_img = Image.open(image_path).convert('RGBA')
            overlay_img = Image.open(overlay_path).convert('RGBA')
            
            # Ensure same size (overlay might be smaller)
            if base_img.size != overlay_img.size:
                overlay_img = overlay_img.resize(base_img.size, Image.Resampling.LANCZOS)
            
            # Merge images
            merged = Image.alpha_composite(base_img, overlay_img)
            
            # Convert back to RGB for JPEG saving
            merged_rgb = merged.convert('RGB')
            merged_rgb.save(output_path, quality=95)
            
            # Preserve original timestamps
            os.utime(output_path, (orig_atime, orig_mtime))
            
            logger.info(f"Merged overlay for {image_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error merging overlay for {image_path.name}: {e}")
            return False
    
    def merge_video_overlay(self, video_path: Path, overlay_path: Path, output_path: Path) -> bool:
        """
        Merge PNG overlay onto video as watermark.
        Returns True if successful, False otherwise.
        """
        if not HAS_CV2:
            logger.error("OpenCV not available - cannot merge video overlays")
            return False
        
        try:
            # Get original timestamps to preserve them
            import os
            orig_atime = os.path.getatime(video_path)
            orig_mtime = os.path.getmtime(video_path)
            
            # Load overlay image with alpha channel
            overlay_img = cv2.imread(str(overlay_path), cv2.IMREAD_UNCHANGED)
            if overlay_img is None:
                logger.error(f"Could not load overlay: {overlay_path}")
                return False
            
            # Extract alpha channel if exists
            if overlay_img.shape[2] == 4:
                overlay_rgb = overlay_img[:, :, :3]
                overlay_alpha = overlay_img[:, :, 3] / 255.0
                overlay_alpha = overlay_alpha[:, :, np.newaxis]  # Add channel dimension for broadcasting
            else:
                overlay_rgb = overlay_img
                overlay_alpha = np.ones((overlay_img.shape[0], overlay_img.shape[1], 1))
            
            # Open video
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                logger.error(f"Could not open video: {video_path}")
                return False
            
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Resize overlay to match video dimensions
            overlay_rgb = cv2.resize(overlay_rgb, (width, height))
            # Resize alpha channel - cv2.resize removes single channel dimension,
            # so we need to handle it properly
            if overlay_alpha.ndim == 3 and overlay_alpha.shape[2] == 1:
                # Single channel array, cv2.resize will return 2D
                overlay_alpha = cv2.resize(overlay_alpha[:, :, 0], (width, height))
                overlay_alpha = overlay_alpha[:, :, np.newaxis]
            else:
                # Already 2D or multi-channel
                overlay_alpha = cv2.resize(overlay_alpha, (width, height))
                if overlay_alpha.ndim == 2:
                    overlay_alpha = overlay_alpha[:, :, np.newaxis]
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            
            if not out.isOpened():
                logger.error(f"Could not create video writer for: {output_path}")
                cap.release()
                return False
            
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Ensure frame is in correct format
                if frame.dtype != np.uint8:
                    frame = frame.astype(np.uint8)
                
                # Apply overlay with alpha blending
                # Convert to float for blending
                frame_float = frame.astype(np.float32)
                overlay_rgb_float = overlay_rgb.astype(np.float32)
                
                # Alpha blending: result = alpha * overlay + (1 - alpha) * frame
                blended = overlay_alpha * overlay_rgb_float + (1 - overlay_alpha) * frame_float
                
                # Convert back to uint8
                blended = np.clip(blended, 0, 255).astype(np.uint8)
                
                out.write(blended)
                frame_count += 1
            
            # Release resources
            cap.release()
            out.release()
            
            # Preserve original timestamps
            os.utime(output_path, (orig_atime, orig_mtime))
            
            logger.info(f"Merged overlay for {video_path.name} ({frame_count} frames)")
            return True
            
        except Exception as e:
            logger.error(f"Error merging video overlay for {video_path.name}: {e}", exc_info=True)
            return False
    
    def process_overlay(self, media_path: Path, output_path: Path, merge_overlays: bool) -> Tuple[bool, Optional[Path]]:
        """
        Process overlay for a media file.
        Returns (success, path_to_processed_file)
        """
        overlay_path = self.find_overlay_for_media(media_path)
        
        # Get original timestamps to preserve them
        import os
        orig_atime = os.path.getatime(media_path)
        orig_mtime = os.path.getmtime(media_path)
        
        if not overlay_path:
            # No overlay found, just copy the file
            try:
                import shutil
                shutil.copy2(media_path, output_path)
                # Preserve original timestamps
                os.utime(output_path, (orig_atime, orig_mtime))
                return True, output_path
            except Exception as e:
                logger.error(f"Error copying {media_path.name}: {e}")
                return False, None
        
        # Overlay found
        if not merge_overlays:
            # User doesn't want overlays, just copy the main file
            try:
                import shutil
                shutil.copy2(media_path, output_path)
                # Preserve original timestamps
                os.utime(output_path, (orig_atime, orig_mtime))
                # Delete overlay file
                overlay_path.unlink(missing_ok=True)
                logger.info(f"Skipped overlay for {media_path.name}")
                return True, output_path
            except Exception as e:
                logger.error(f"Error processing {media_path.name}: {e}")
                return False, None
        
        # Merge overlay
        if media_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            success = self.merge_image_overlay(media_path, overlay_path, output_path)
        elif media_path.suffix.lower() == '.mp4':
            success = self.merge_video_overlay(media_path, overlay_path, output_path)
        else:
            logger.warning(f"Unsupported file type for overlay: {media_path}")
            success = False
        
        # Delete overlay file after merging
        if success:
            overlay_path.unlink(missing_ok=True)
        
        return success, output_path if success else None