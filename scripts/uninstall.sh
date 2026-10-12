#!/usr/bin/env bash
set -euo pipefail

# uninstall.sh: Cross-platform uninstaller for macOS and Linux
# Removes the SDLC Azure Agent CLI (`agent`) globally.

echo "==> Uninstalling ado-sdlc-agent globally..."

uninstalled=0

if command -v uv >/dev/null 2>&1; then
    if uv tool list 2>/dev/null | grep -q "ado-sdlc-agent"; then
        echo "==> Removing via uv tool..."
        uv tool uninstall ado-sdlc-agent
        uninstalled=1
    fi
fi

if command -v pipx >/dev/null 2>&1; then
    if pipx list 2>/dev/null | grep -q "ado-sdlc-agent"; then
        echo "==> Removing via pipx..."
        pipx uninstall ado-sdlc-agent
        uninstalled=1
    fi
fi

if command -v pip >/dev/null 2>&1; then
    if pip show ado-sdlc-agent >/dev/null 2>&1; then
        echo "==> Removing via pip..."
        pip uninstall -y ado-sdlc-agent
        uninstalled=1
    fi
elif command -v python3 >/dev/null 2>&1; then
    if python3 -m pip show ado-sdlc-agent >/dev/null 2>&1; then
        echo "==> Removing via python3 -m pip..."
        python3 -m pip uninstall -y ado-sdlc-agent
        uninstalled=1
    fi
fi

if [ "$uninstalled" -eq 1 ]; then
    echo ""
    echo "[OK] Successfully uninstalled ado-sdlc-agent."
else
    echo ""
    echo "[INFO] No global installation of ado-sdlc-agent found to remove."
fi
