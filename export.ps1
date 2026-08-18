# This script packages your project cleanly into a zip file on your Desktop, 
# ignoring the massive node_modules and venv directories.
Write-Host "Zipping DermaCare project..." -ForegroundColor Cyan

$sourcePath = $PSScriptRoot
$destinationZip = Join-Path (Split-Path $PSScriptRoot -Parent) "DermaCare_Project.zip"

# Clean up previous zip if it exists
if (Test-Path $destinationZip) { Remove-Item $destinationZip }

# Create a temporary directory to copy allowed files
$tempDir = Join-Path $env:TEMP "DermaCare_Export"
if (Test-Path $tempDir) { Remove-Item -Recurse -Force $tempDir }
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copy files while explicitly excluding target heavy directories
Get-ChildItem -Path $sourcePath -Recurse | Where-Object {
    $_.FullName -notmatch "\\node_modules\\" -and
    $_.FullName -notmatch "\\\.next\\" -and
    $_.FullName -notmatch "\\venv\\" -and
    $_.FullName -notmatch "\\__pycache__\\"
} | Copy-Item -Destination {
    $dest = $_.FullName.Replace($sourcePath, $tempDir)
    $parent = Split-Path $dest
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent | Out-Null }
    $dest
} -Force

# Zip the payload
Compress-Archive -Path "$tempDir\*" -DestinationPath $destinationZip -Force

# Cleanup temp folder
Remove-Item -Recurse -Force $tempDir

Write-Host "Success! Clean export saved to: $destinationZip" -ForegroundColor Green
