# Building fabric-launcher Package

This guide explains how to build the fabric-launcher package from source.

## Prerequisites

1. **Python 3.9 or higher** must be installed
   - Download from: https://www.python.org/downloads/
   - Or use Anaconda/Miniconda
   - Verify installation: `python --version`

2. **Build tools** (will be installed in step 2 below)
   - build
   - wheel
   - setuptools

## Build Steps

### 1. Install Build Dependencies

```powershell
# Navigate to the project directory
cd c:\GitHub\fabric-launcher

# Install/upgrade build tools
python -m pip install --upgrade build wheel setuptools
```

### 2. Build the Package

```powershell
# Build both source distribution and wheel
python -m build
```

This will create two files in the `dist/` directory:
- `fabric-launcher-0.3.0.tar.gz` (source distribution)
- `fabric_launcher-0.3.0-py3-none-any.whl` (wheel distribution)

### 3. Verify the Build

```powershell
# Check the dist directory
dir dist\

# You should see:
# - fabric-launcher-0.3.0.tar.gz
# - fabric_launcher-0.3.0-py3-none-any.whl
```

## Alternative: Build Using setuptools Directly

```powershell
# Build wheel only
python setup.py bdist_wheel

# Build source distribution only
python setup.py sdist

# Build both
python setup.py sdist bdist_wheel
```

Note: Using `python -m build` is the recommended modern approach.

## Installing the Built Package Locally

After building, you can install the package locally for testing:

```powershell
# Install from wheel
python -m pip install dist\fabric_launcher-0.3.0-py3-none-any.whl

# Or install in development mode (editable install)
python -m pip install -e .
```

## Publishing to PyPI

### Test PyPI (recommended for testing)

```powershell
# Install twine
python -m pip install --upgrade twine

# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*

# Test installation from Test PyPI
python -m pip install --index-url https://test.pypi.org/simple/ fabric-launcher
```

### Production PyPI

```powershell
# Upload to PyPI (requires credentials)
python -m twine upload dist/*
```

## Cleaning Build Artifacts

```powershell
# Remove build directories
Remove-Item -Recurse -Force build, dist, *.egg-info -ErrorAction SilentlyContinue
```

## Troubleshooting

### Python Not Found

If you get "python is not recognized", you need to install Python:
1. Download from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Restart your terminal

### Build Module Not Found

```powershell
python -m pip install build
```

### Permission Errors

Run PowerShell as Administrator or use:
```powershell
python -m pip install --user build wheel setuptools
```

## Automated Build Script

For convenience, you can use this PowerShell script:

```powershell
# build.ps1
$ErrorActionPreference = "Stop"

Write-Host "Installing build dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade build wheel setuptools

Write-Host "Cleaning previous builds..." -ForegroundColor Cyan
Remove-Item -Recurse -Force build, dist, *.egg-info -ErrorAction SilentlyContinue

Write-Host "Building package..." -ForegroundColor Cyan
python -m build

Write-Host "Build complete!" -ForegroundColor Green
Write-Host "Built packages:" -ForegroundColor Green
Get-ChildItem dist\ | ForEach-Object { Write-Host "  - $($_.Name)" }
```

Save this as `build.ps1` and run:
```powershell
.\build.ps1
```

## CI/CD Build

The package includes GitHub Actions workflow (`.github/workflows/tests.yml`) that automatically:
- Runs tests on every push
- Tests on Python 3.9, 3.10, 3.11, 3.12
- Tests on Ubuntu, Windows, macOS

To add automated package building to CI/CD, create `.github/workflows/build.yml`.

## Version Management

The package version is defined in `pyproject.toml`:

```toml
[project]
name = "fabric-launcher"
version = "0.3.0"
```

Before building a new release:
1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with release notes
3. Commit changes
4. Tag the release: `git tag v0.3.0`
5. Build and publish

## Package Contents

The built package includes:
- `fabric_launcher/` - Main package code
  - `__init__.py`
  - `launcher.py`
  - `github_downloader.py`
  - `fabric_deployer.py`
  - `file_operations.py`
  - `notebook_executor.py`
  - `config_manager.py`
  - `deployment_validator.py`
  - `deployment_report.py`
- `README.md` - Package documentation
- `LICENSE` - MIT License
- `CHANGELOG.md` - Version history

## Build Output Example

```
Successfully built fabric-launcher-0.3.0.tar.gz and fabric_launcher-0.3.0-py3-none-any.whl
```

## Next Steps

After building:
1. **Test locally**: Install in a virtual environment and test
2. **Run tests**: `pytest tests/`
3. **Test PyPI**: Upload to Test PyPI first
4. **Production**: Upload to PyPI when ready
