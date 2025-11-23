@echo off
REM Build script for fabric-launcher package
REM Usage: build.bat

echo.
echo ========================================
echo fabric-launcher Package Build Script
echo ========================================
echo.

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    exit /b 1
)
python --version
echo.

REM Install build dependencies
echo Installing build dependencies...
python -m pip install --upgrade pip build wheel setuptools --quiet
if errorlevel 1 (
    echo ERROR: Failed to install build dependencies
    exit /b 1
)
echo Build dependencies installed.
echo.

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d %%i in (*.egg-info) do rmdir /s /q "%%i"
echo Build artifacts cleaned.
echo.

REM Build the package
echo Building package...
python -m build
if errorlevel 1 (
    echo ERROR: Build failed
    exit /b 1
)
echo.

REM Display results
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Built packages in dist/:
dir /b dist\
echo.
echo Next steps:
echo   1. Test locally:  pip install dist\fabric_launcher-0.3.0-py3-none-any.whl
echo   2. Run tests:     pytest tests/
echo   3. Upload to PyPI: python -m twine upload dist/*
echo.
