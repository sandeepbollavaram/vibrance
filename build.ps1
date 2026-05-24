#requires -Version 5.1
<#
.SYNOPSIS
    Build Vibrance.exe and the Inno Setup installer locally.

.NOTES
    Requires Python 3.10+, PyInstaller, and Inno Setup 6 (iscc on PATH).
    Run from the repo root:
        .\build.ps1
        .\build.ps1 -Version 1.2.0
#>

param(
    [string]$Version = "1.0.0",
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

# 1. Venv
if (-not (Test-Path .\.venv)) {
    Write-Host "Creating venv..." -ForegroundColor Cyan
    python -m venv .venv
}
$py = ".\.venv\Scripts\python.exe"

Write-Host "Installing build deps..." -ForegroundColor Cyan
& $py -m pip install --upgrade pip --quiet
& $py -m pip install -r requirements-dev.txt --quiet

# 2. Icon
if (-not (Test-Path .\src\image_editor\resources\app.ico)) {
    Write-Host "Generating placeholder icon..." -ForegroundColor Cyan
    & $py scripts\make_icon.py
}

# 3. Clean
Write-Host "Cleaning previous build..." -ForegroundColor Cyan
Remove-Item -Recurse -Force .\build, .\dist -ErrorAction SilentlyContinue
Remove-Item -Force .\Vibrance.spec -ErrorAction SilentlyContinue

# 4. PyInstaller
Write-Host "Building Vibrance.exe..." -ForegroundColor Cyan
& $py -m PyInstaller `
    --noconsole `
    --onefile `
    --clean `
    --name Vibrance `
    --icon src\image_editor\resources\app.ico `
    --add-data "src\image_editor\resources;image_editor\resources" `
    -p src `
    src\image_editor\__main__.py

if (-not (Test-Path .\dist\Vibrance.exe)) {
    throw "PyInstaller did not produce dist\Vibrance.exe"
}
Write-Host "  -> dist\Vibrance.exe" -ForegroundColor Green

# 5. Installer
if ($SkipInstaller) {
    Write-Host "Skipping installer (--SkipInstaller)." -ForegroundColor Yellow
    return
}

$iscc = (Get-Command iscc -ErrorAction SilentlyContinue)?.Source
if (-not $iscc) {
    $iscc = "C:\Program Files (x86)\Inno Setup 6\iscc.exe"
    if (-not (Test-Path $iscc)) {
        Write-Warning "Inno Setup not found. Install from https://jrsoftware.org/isinfo.php and re-run."
        return
    }
}

Write-Host "Compiling installer..." -ForegroundColor Cyan
& $iscc "/DMyAppVersion=$Version" installer.iss
$installer = ".\dist\Vibrance_Setup_$Version.exe"
if (Test-Path $installer) {
    Write-Host "  -> $installer" -ForegroundColor Green
} else {
    Write-Warning "Installer not found at expected path."
}
