@echo off
REM Windows build script for Snapchat Memory Fixer
REM Run this on a Windows machine with Python and PyInstaller installed

echo === Building Snapchat Memory Fixer for Windows ===

REM Get version from version.py
for /f "tokens=*" %%i in ('python -c "import sys; sys.path.insert(0, 'src'); from version import VERSION; print(VERSION)"') do set VERSION=%%i
echo Building version: %VERSION%

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Build with PyInstaller
echo Building executable with PyInstaller...
pyinstaller ^
    --name=snapmemoryfixer ^
    --onefile ^
    --windowed ^
    --paths=src ^
    --add-data="exiftool\exiftool-13.55_64\exiftool(-k).exe;exiftool\exiftool-13.55_64" ^
    --add-data="exiftool\exiftool-13.55_64\exiftool_files;exiftool\exiftool-13.55_64\exiftool_files" ^
    --hidden-import=PIL ^
    --hidden-import=PIL._imaging ^
    --hidden-import=cv2 ^
    --hidden-import=dateutil ^
    --hidden-import=dateutil.parser ^
    --hidden-import=dateutil.relativedelta ^
    --hidden-import=dateutil.tz ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.filedialog ^
    --hidden-import=tkinter.messagebox ^
    --hidden-import=tkinter.scrolledtext ^
    --hidden-import=queue ^
    --hidden-import=threading ^
    --hidden-import=logging ^
    --hidden-import=json ^
    --hidden-import=pathlib ^
    --hidden-import=typing ^
    --hidden-import=datetime ^
    --hidden-import=os ^
    --hidden-import=sys ^
    --hidden-import=subprocess ^
    --clean ^
    main.py

echo.
echo === Build completed successfully! ===
echo Executable created at: dist\snapmemoryfixer.exe
echo.

REM Create README for Windows
echo Creating README file...
(
echo Snapchat Memory Fixer v%VERSION% - Windows Portable Edition
echo ===========================================================
echo.
echo This is a portable executable for fixing Snapchat memories export files.
echo.
echo Usage:
echo   Double-click snapmemoryfixer.exe
echo.
echo Features:
echo   - Fix metadata for Snapchat memories exported as zip files
echo   - Merge overlays (text, drawings, filters) with media files
echo   - Update EXIF data with correct dates from JSON metadata
echo   - Organize files with snapMemory_ prefix
echo.
echo Requirements:
echo   - Windows 7 or later
echo   - .NET Framework (usually pre-installed)
echo.
echo How to use:
echo 1. Double-click snapmemoryfixer.exe
echo 2. Add your Snapchat export zip files
echo 3. Select output directory
echo 4. Click "Start Processing"
echo.
echo For more information, visit the GitHub repository.
) > dist\README.txt

echo Creating Windows ZIP archive...
cd dist
"C:\Program Files\7-Zip\7z.exe" a -tzip ..\snapmemoryfixer-v%VERSION%-windows-portable.zip snapmemoryfixer.exe README.txt
cd ..

echo.
echo === Release package created! ===
echo Archive: snapmemoryfixer-v%VERSION%-windows-portable.zip
echo.
echo To distribute:
echo   1. Upload snapmemoryfixer-v%VERSION%-windows-portable.zip to GitHub Releases
echo   2. Users can download and extract the ZIP file
echo   3. Then double-click: snapmemoryfixer.exe
echo.
echo Build process completed successfully!
pause