#!/bin/bash

echo "Installing packages..."

if which apt > /dev/null 2>&1; then
    sudo apt update
    sudo apt install -y curl wget git unzip python3 python3-pip python3-requests
elif which dnf > /dev/null 2>&1; then
    sudo dnf install -y curl wget git unzip python3 python3-pip python3-requests
elif which pacman > /dev/null 2>&1; then
    sudo pacman -S --noconfirm curl wget git unzip python python-pip python-requests
else
    echo "Unsupported system"
    exit 1
fi

python3 -c "import requests"
if [ $? -ne 0 ]; then
    echo "requests not found, trying pip"
    pip3 install requests --break-system-packages
fi

echo "Downloading installer.py..."
curl -L -o installer.py https://raw.githubusercontent.com/DevOS-create/PocketTux/main/installer.py

if [ ! -f installer.py ]; then
    echo "Download failed"
    exit 1
fi

echo "Running installer.py..."
python3 installer.py
