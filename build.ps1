# Build script for fabric-launcher package
# Usage: .\build.ps1

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "fabric-launcher Package Build Script" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.9+ from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Red
    exit 1
}

# Install/upgrade build dependencies
Write-Host "`nInstalling build dependencies..." -ForegroundColor Yellow
try {
    & python -m pip install --upgrade pip build wheel setuptools --quiet
    Write-Host "[OK] Build dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to install build dependencies" -ForegroundColor Red
    exit 1
}

# Clean previous builds
Write-Host "`nCleaning previous builds..." -ForegroundColor Yellow
$itemsToRemove = @("build", "dist", "*.egg-info")
foreach ($item in $itemsToRemove) {
    if (Test-Path $item) {
        Remove-Item -Recurse -Force $item
        Write-Host "  Removed: $item" -ForegroundColor Gray
    }
}
Write-Host "[OK] Build artifacts cleaned" -ForegroundColor Green

# Build the package
Write-Host "`nBuilding package..." -ForegroundColor Yellow
try {
    & python -m build
    Write-Host "[OK] Package built successfully!" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Build failed" -ForegroundColor Red
    exit 1
}

# Display build results
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Build Complete!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if (Test-Path "dist") {
    Write-Host "Built packages in dist/:" -ForegroundColor Green
    Get-ChildItem dist\ | ForEach-Object {
        $size = [math]::Round($_.Length / 1KB, 2)
        Write-Host "  [+] $($_.Name) - $size KB" -ForegroundColor Green
    }
} else {
    Write-Host "Warning: dist/ directory not found" -ForegroundColor Yellow
}

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Test locally:  pip install dist\fabric_launcher-0.3.0-py3-none-any.whl" -ForegroundColor White
Write-Host "  2. Run tests:     pytest tests/" -ForegroundColor White
Write-Host "  3. Upload to PyPI: python -m twine upload dist/*" -ForegroundColor White
Write-Host ""
