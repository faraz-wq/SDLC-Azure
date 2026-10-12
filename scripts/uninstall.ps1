# uninstall.ps1: Windows PowerShell uninstaller
# Removes the SDLC Azure Agent CLI (`agent`) globally.

$ErrorActionPreference = "SilentlyContinue"

Write-Host "==> Uninstalling ado-sdlc-agent globally..." -ForegroundColor Cyan

$uninstalled = $false

if (Get-Command "uv" -ErrorAction SilentlyContinue) {
    $uvList = uv tool list 2>$null
    if ($uvList -match "ado-sdlc-agent") {
        Write-Host "==> Removing via uv tool..." -ForegroundColor Green
        uv tool uninstall ado-sdlc-agent
        $uninstalled = $true
    }
}

if (Get-Command "pipx" -ErrorAction SilentlyContinue) {
    $pipxList = pipx list 2>$null
    if ($pipxList -match "ado-sdlc-agent") {
        Write-Host "==> Removing via pipx..." -ForegroundColor Green
        pipx uninstall ado-sdlc-agent
        $uninstalled = $true
    }
}

if (Get-Command "pip" -ErrorAction SilentlyContinue) {
    $pipShow = pip show ado-sdlc-agent 2>$null
    if ($pipShow) {
        Write-Host "==> Removing via pip..." -ForegroundColor Green
        pip uninstall -y ado-sdlc-agent
        $uninstalled = $true
    }
} elseif (Get-Command "python" -ErrorAction SilentlyContinue) {
    $pyShow = python -m pip show ado-sdlc-agent 2>$null
    if ($pyShow) {
        Write-Host "==> Removing via python -m pip..." -ForegroundColor Green
        python -m pip uninstall -y ado-sdlc-agent
        $uninstalled = $true
    }
}

if ($uninstalled) {
    Write-Host ""
    Write-Host "[OK] Successfully uninstalled ado-sdlc-agent." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[INFO] No global installation of ado-sdlc-agent found to remove." -ForegroundColor Yellow
}
