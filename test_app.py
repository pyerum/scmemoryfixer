#!/usr/bin/env python3
"""
Simple test script for Snapchat Memory Fixer
"""

import sys
import os
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from utils import extract_uuid_from_filename, extract_uuid_from_url

def test_uuid_extraction():
    """Test UUID extraction functions."""
    print("Testing UUID extraction...")
    
    # Test filename extraction
    test_filename = "2024-01-15-12345678-1234-1234-1234-123456789012-main.jpg"
    uuid = extract_uuid_from_filename(test_filename)
    print(f"  Filename: {test_filename}")
    print(f"  Extracted UUID: {uuid}")
    
    expected = "12345678-1234-1234-1234-123456789012"
    assert uuid == expected, f"Expected {expected}, got {uuid}"
    
    # Test URL extraction
    test_url = "https://something.com/?param=value&mid=87654321-4321-4321-4321-210987654321&tid=something"
    uuid = extract_uuid_from_url(test_url)
    print(f"  URL: {test_url}")
    print(f"  Extracted UUID: {uuid}")
    
    expected = "87654321-4321-4321-4321-210987654321"
    assert uuid == expected, f"Expected {expected}, got {uuid}"
    
    print("  ✓ UUID extraction tests passed!")

def test_imports():
    """Test that all modules can be imported."""
    print("\nTesting module imports...")
    
    modules = [
        "utils",
        "metadata",
        "overlay", 
        "processor",
        "gui"
    ]
    
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name} imports successfully")
        except ImportError as e:
            print(f"  ✗ {module_name} import failed: {e}")
            return False
    
    return True

def main():
    """Run tests."""
    print("=" * 60)
    print("Snapchat Memory Fixer - Test Script")
    print("=" * 60)
    
    try:
        # Test imports
        if not test_imports():
            print("\n✗ Some imports failed")
            return 1
        
        # Test UUID extraction
        test_uuid_extraction()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
        # Try to create a processor instance
        print("\nTesting processor initialization...")
        from processor import MemoryProcessor
        processor = MemoryProcessor()
        print("  ✓ Processor initialized successfully")
        
        # Check if we can read the example zip
        example_zip = Path("exportExample/mydata~1775490456493.zip")
        if example_zip.exists():
            print(f"\nExample zip file found: {example_zip}")
            print(f"Size: {example_zip.stat().st_size / (1024*1024):.2f} MB")
            
            # Try to list contents
            import zipfile
            try:
                with zipfile.ZipFile(example_zip, 'r') as zf:
                    files = zf.namelist()
                    print(f"\nZip contains {len(files)} files")
                    
                    # Find JSON file
                    json_files = [f for f in files if 'memories_history.json' in f]
                    if json_files:
                        print(f"  Found JSON file: {json_files[0]}")
                    
                    # Find media files
                    media_files = [f for f in files if any(ext in f.lower() for ext in ['.jpg', '.jpeg', '.mp4', '.png'])]
                    print(f"  Found {len(media_files)} media files")
                    
                    # Show some examples
                    if media_files:
                        print(f"  Example media files:")
                        for f in media_files[:3]:
                            print(f"    - {f}")
                    
            except Exception as e:
                print(f"  ✗ Error reading zip: {e}")
        else:
            print("\n✗ Example zip file not found")
        
        print("\n" + "=" * 60)
        print("Application is ready to run!")
        print("To start the GUI, run: python main.py")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())