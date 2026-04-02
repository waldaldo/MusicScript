#!/usr/bin/env bash
set -euo pipefail

SOCKET="/tmp/mpv_radio_socket"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -S "$SOCKET" ]; then
    exec "$SCRIPT_DIR/wofi_controls.sh"
else
    exec "$SCRIPT_DIR/wofi_launcher.sh"
fi
