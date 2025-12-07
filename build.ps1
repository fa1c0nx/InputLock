function Command-Exists {
    param([string]$cmd)
    $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

Write-Host "Checking dependencies..."

if (-not (Command-Exists python)) {
    Write-Host "Python not found. Installing via winget..."
    winget install -e --id Python.Python.3.11 --source winget
    if (-not (Command-Exists python)) { throw "Python installation failed." }
} else { Write-Host "Python found." }

if (-not (Command-Exists go)) {
    Write-Host "Go not found. Installing via winget..."
    winget install -e --id GoLang.Go --source winget
    if (-not (Command-Exists go)) { throw "Go installation failed." }
} else { Write-Host "Go found." }

Write-Host "Installing Python dependencies..."
try {
    python -m pip install --upgrade pip
    python -m pip install -r src/requirements.txt
    python -m pip install pyinstaller pillow pystray keyboard psutil
} catch { throw "Python dependencies installation failed." }

if (-not (Test-Path build)) { New-Item -ItemType Directory build }

Write-Host "Building Python executable..."
try {
    & python -m PyInstaller --onefile --noconsole --distpath build --name InputLock src/main.py
} catch { throw "Python build failed." }

Write-Host "Building Go hook..."
try {
    Push-Location src/hook
    go build -o ../../build/hook.exe hook.go
    Pop-Location
} catch { throw "Go build failed." }

Write-Host "Cleaning up PyInstaller temp folder..."
$pyInstallerTemp = Join-Path build "InputLock"
if (Test-Path $pyInstallerTemp) { Remove-Item -Recurse -Force $pyInstallerTemp }

Write-Host "Build completed successfully! Check the build/ folder."
