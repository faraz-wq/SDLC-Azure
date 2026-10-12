# install.ps1: Windows PowerShell installer
# Installs the SDLC Azure Agent CLI globally as `agent`.

$ErrorActionPreference = "Stop"

Write-Host "==> Detecting package manager..." -ForegroundColor Cyan

if (Get-Command "uv" -ErrorAction SilentlyContinue) {
    Write-Host "==> uv detected. Installing ado-sdlc-agent globally via uv tool..." -ForegroundColor Green
    uv tool install . --force
} elseif (Get-Command "pipx" -ErrorAction SilentlyContinue) {
    Write-Host "==> pipx detected. Installing ado-sdlc-agent globally via pipx..." -ForegroundColor Green
    pipx install . --force
} elseif (Get-Command "pip" -ErrorAction SilentlyContinue) {
    Write-Host "==> Installing ado-sdlc-agent via pip..." -ForegroundColor Green
    pip install .
} elseif (Get-Command "python" -ErrorAction SilentlyContinue) {
    Write-Host "==> Installing ado-sdlc-agent via python -m pip..." -ForegroundColor Green
    python -m pip install .
} else {
    Write-Error "ERROR: Neither uv, pipx, pip, nor python was found on PATH. Please install Python >= 3.12 or uv (https://docs.astral.sh/uv/)."
    exit 1
}

Write-Host ""
Write-Host "[OK] Installation complete! The 'agent' command is ready." -ForegroundColor Green
Write-Host "     Run 'agent --help' to verify."
