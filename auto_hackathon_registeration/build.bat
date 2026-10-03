@echo off
REM ==============================================================================
REM HackFill - Windows Executable Build Script
REM Builds HackFill.exe using PyInstaller
REM ==============================================================================

echo [HackFill] Starting Build Process...

REM 1. Activate Virtual Environment if present
if exist ".venv\Scripts\activate.bat" (
    echo [HackFill] Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM 2. Ensure PyInstaller is installed
echo [HackFill] Checking PyInstaller...
python -m pip install pyinstaller

REM 3. Clean previous build artifacts
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "HackFill.spec" del HackFill.spec

REM 4. Execute PyInstaller
echo [HackFill] Compiling HackFill with PyInstaller...
pyinstaller --noconfirm --onedir --windowed ^
    --name "HackFill" ^
    --add-data "profiles;profiles" ^
    --add-data "test_pages;test_pages" ^
    --hidden-import "playwright" ^
    --hidden-import "playwright.sync_api" ^
    --hidden-import "PySide6" ^
    --hidden-import "PySide6.QtCore" ^
    --hidden-import "PySide6.QtGui" ^
    --hidden-import "PySide6.QtWidgets" ^
    main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================================================================
    echo [HackFill] BUILD SUCCESSFUL!
    echo Executable generated at: dist\HackFill\HackFill.exe
    echo Note: Ensure Playwright browsers are installed: playwright install chromium
    echo ==============================================================================
) else (
    echo.
    echo [HackFill] BUILD FAILED! Check error messages above.
)
pause
