"""
Cross-platform file dialog module for Snapchat Memory Fixer.
Provides native file/folder pickers for Linux, macOS, and Windows.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Platform detection
IS_LINUX = sys.platform.startswith('linux')
IS_MACOS = sys.platform == 'darwin'
IS_WINDOWS = sys.platform.startswith('win')


def find_zenity() -> Optional[str]:
    """Find zenity executable path."""
    try:
        result = subprocess.run(['which', 'zenity'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return None


def find_kdialog() -> Optional[str]:
    """Find kdialog executable path."""
    try:
        result = subprocess.run(['which', 'kdialog'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return None


def find_yad() -> Optional[str]:
    """Find yad executable path."""
    try:
        result = subprocess.run(['which', 'yad'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return None


def use_native_dialogs() -> bool:
    """Check if native dialogs should be used."""
    if IS_WINDOWS:
        return False  # Windows native dialogs are more complex, stick with tkinter
    
    if IS_MACOS:
        # Check if osascript is available (it should be on macOS)
        try:
            result = subprocess.run(['which', 'osascript'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    if IS_LINUX:
        # Check for native dialog tools
        return bool(find_zenity() or find_kdialog() or find_yad())
    
    return False


def ask_open_filenames(title: str = "Select Files", filetypes: List[Tuple[str, str]] = None) -> List[Path]:
    """
    Open native file dialog to select one or more files.
    Returns list of selected file paths.
    Falls back to tkinter if native dialogs unavailable.
    """
    if not use_native_dialogs():
        logger.debug("Native dialogs not available, using tkinter fallback")
        return _tkinter_ask_open_filenames(title, filetypes)
    
    if IS_MACOS:
        return _macos_ask_open_filenames(title, filetypes)
    elif IS_LINUX:
        return _linux_ask_open_filenames(title, filetypes)
    else:
        return _tkinter_ask_open_filenames(title, filetypes)


def ask_saveas_filename(title: str = "Select Folder", initialfile: str = "") -> Optional[Path]:
    """
    Open native file dialog to select a folder for saving.
    Returns selected folder path.
    Falls back to tkinter if native dialogs unavailable.
    """
    if not use_native_dialogs():
        logger.debug("Native dialogs not available, using tkinter fallback")
        return _tkinter_ask_saveas_filename(title)
    
    if IS_MACOS:
        return _macos_ask_saveas_filename(title)
    elif IS_LINUX:
        return _linux_ask_saveas_filename(title)
    else:
        return _tkinter_ask_saveas_filename(title)


def _tkinter_ask_open_filenames(title: str = "Select Files", filetypes: List[Tuple[str, str]] = None) -> List[Path]:
    """Fallback to tkinter file dialog."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        files = filedialog.askopenfilenames(
            title=title,
            filetypes=filetypes or [("All files", "*.*")]
        )
        root.destroy()
        
        return [Path(f) for f in files]
    except Exception as e:
        logger.error(f"tkinter file dialog failed: {e}")
        return []


def _tkinter_ask_saveas_filename(title: str = "Select Folder") -> Optional[Path]:
    """Fallback to tkinter folder dialog."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        folder = filedialog.askdirectory(title=title)
        root.destroy()
        
        return Path(folder) if folder else None
    except Exception as e:
        logger.error(f"tkinter folder dialog failed: {e}")
        return None


def _linux_ask_open_filenames(title: str = "Select Files", filetypes: List[Tuple[str, str]] = None) -> List[Path]:
    """Use Linux native file dialogs (zenity/kdialog/yad)."""
    # Try zenity first
    zenity_path = find_zenity()
    if zenity_path:
        return _zenity_ask_open_filenames(title, filetypes)
    
    # Try kdialog
    kdialog_path = find_kdialog()
    if kdialog_path:
        return _kdialog_ask_open_filenames(title, filetypes)
    
    # Try yad
    yad_path = find_yad()
    if yad_path:
        return _yad_ask_open_filenames(title, filetypes)
    
    return _tkinter_ask_open_filenames(title, filetypes)


def _linux_ask_saveas_filename(title: str = "Select Folder") -> Optional[Path]:
    """Use Linux native folder dialog (zenity/kdialog/yad)."""
    # Try zenity first
    zenity_path = find_zenity()
    if zenity_path:
        return _zenity_ask_saveas_filename(title)
    
    # Try kdialog
    kdialog_path = find_kdialog()
    if kdialog_path:
        return _kdialog_ask_saveas_filename(title)
    
    # Try yad
    yad_path = find_yad()
    if yad_path:
        return _yad_ask_saveas_filename(title)
    
    return _tkinter_ask_saveas_filename(title)


def _zenity_ask_open_filenames(title: str = "Select Files", filetypes: List[Tuple[str, str]] = None) -> List[Path]:
    """Use zenity file dialog."""
    try:
        cmd = ['zenity', '--file-selection', '--title', title, '--multiple']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            files = result.stdout.strip().split('|')
            return [Path(f) for f in files if f]
    except Exception as e:
        logger.error(f"zenity file dialog failed: {e}")
    
    return []


def _zenity_ask_saveas_filename(title: str = "Select Folder") -> Optional[Path]:
    """Use zenity folder dialog."""
    try:
        cmd = ['zenity', '--file-selection', '--title', title, '--directory']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            folder = result.stdout.strip()
            return Path(folder) if folder else None
    except Exception as e:
        logger.error(f"zenity folder dialog failed: {e}")
    
    return None


def _kdialog_ask_open_filenames(title: str = "Select Files", filetypes: List[Tuple[str, str]] = None) -> List[Path]:
    """Use kdialog file dialog."""
    try:
        cmd = ['kdialog', '--getopenfilename', '', title]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            files = result.stdout.strip().split('\n')
            return [Path(f) for f in files if f and f != 'file://']
    except Exception as e:
        logger.error(f"kdialog file dialog failed: {e}")
    
    return []


def _kdialog_ask_saveas_filename(title: str = "Select Folder") -> Optional[Path]:
    """Use kdialog folder dialog."""
    try:
        cmd = ['kdialog', '--getexistingdirectory', '', title]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            folder = result.stdout.strip()
            return Path(folder) if folder else None
    except Exception as e:
        logger.error(f"kdialog folder dialog failed: {e}")
    
    return None


def _yad_ask_open_filenames(title: str = "Select Files", filetypes: List[Tuple[str, str]] = None) -> List[Path]:
    """Use yad file dialog."""
    try:
        cmd = ['yad', '--file-selection', '--title', title, '--multiple']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            files = result.stdout.strip().split('|')
            return [Path(f) for f in files if f]
    except Exception as e:
        logger.error(f"yad file dialog failed: {e}")
    
    return []


def _yad_ask_saveas_filename(title: str = "Select Folder") -> Optional[Path]:
    """Use yad folder dialog."""
    try:
        cmd = ['yad', '--file-selection', '--title', title, '--directory']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            folder = result.stdout.strip()
            return Path(folder) if folder else None
    except Exception as e:
        logger.error(f"yad folder dialog failed: {e}")
    
    return None


def _macos_ask_open_filenames(title: str = "Select Files", filetypes: List[Tuple[str, str]] = None) -> List[Path]:
    """Use macOS AppleScript file dialog."""
    try:
        # Build AppleScript for file selection
        script = f'''
        tell application "System Events"
            activate
            set selectedFiles to choose file with prompt "{title}" with multiple selections allowed
            set filePaths to {{}}
            repeat with aFile in selectedFiles
                set end of filePaths to POSIX path of (aFile as text)
            end repeat
            return filePaths
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            files = result.stdout.strip().split(', ')
            return [Path(f) for f in files if f]
    except Exception as e:
        logger.error(f"macOS file dialog failed: {e}")
    
    return []


def _macos_ask_saveas_filename(title: str = "Select Folder") -> Optional[Path]:
    """Use macOS AppleScript folder dialog."""
    try:
        script = f'''
        tell application "System Events"
            activate
            set selectedFolder to choose folder with prompt "{title}"
            return POSIX path of (selectedFolder as text)
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            folder = result.stdout.strip()
            return Path(folder) if folder else None
    except Exception as e:
        logger.error(f"macOS folder dialog failed: {e}")
    
    return None