#!/usr/bin/env bash
set -euo pipefail

# install.sh: Cross-platform installer for macOS and Linux
# Installs the SDLC Azure Agent CLI globally as `agent`.

echo "==> Detecting package manager..."

if command -v uv >/dev/null 2>&1; then
    echo "==> uv detected. Installing ado-sdlc-agent globally via uv tool..."
    uv tool install . --force
elif command -v pipx >/dev/null 2>&1; then
    echo "==> pipx detected. Installing ado-sdlc-agent globally via pipx..."
    pipx install . --force
elif command -v pip >/dev/null 2>&1; then
    echo "==> Installing ado-sdlc-agent via pip..."
    pip install .
elif command -v python3 >/dev/null 2>&1; then
    echo "==> Installing ado-sdlc-agent via python3 -m pip..."
    python3 -m pip install .
else
    echo "ERROR: Neither uv, pipx, pip, nor python3 was found on PATH." >&2
    echo "Please install Python >= 3.12 or uv (https://docs.astral.sh/uv/)." >&2
    exit 1
fi

echo ""
echo "[OK] Installation complete! The 'agent' command is ready."
echo "     Run 'agent --help' to verify."
