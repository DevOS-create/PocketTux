#!/bin/bash
set -euo pipefail
trap 'echo "Failed at line $LINENO" >&2' ERR

URL="https://raw.githubusercontent.com/DevOS-create/PocketTux/main/installer.py"
DIR="$HOME/PocketTux-setup"

[ "$(id -u)" -eq 0 ] || command -v sudo >/dev/null || { echo "Need root or sudo" >&2; exit 1; }

if command -v apt >/dev/null; then
    sudo apt update && sudo apt install -y curl python3 python3-requests
elif command -v dnf >/dev/null; then
    sudo dnf install -y curl python3 python3-requests
elif command -v pacman >/dev/null; then
    sudo pacman -S --noconfirm curl python python-requests
else
    echo "Unsupported distro" >&2
    exit 1
fi

mkdir -p "$DIR" && cd "$DIR"
curl -fsSL -o installer.py "$URL"
[ -s installer.py ] || { echo "Download failed" >&2; exit 1; }

python3 -c "import requests" || { echo "python requests missing" >&2; exit 1; }

python3 installer.py
