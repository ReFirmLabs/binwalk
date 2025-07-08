#!/bin/bash
# Install pip dependencies.
# Requires that pip3 is already installed.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v uv >/dev/null 2>&1; then
    uv pip install -r "$SCRIPT_DIR/requirements.txt"
else
    pip install -r "$SCRIPT_DIR/requirements.txt" --break-system-packages
fi
