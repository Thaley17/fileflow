#!/bin/bash
# Quick start — runs FileFlow in the foreground
# For background mode, use: fileflow start
cd "$(dirname "$0")"
pip3 install -q flask markdown markupsafe 2>/dev/null
mkdir -p ~/FileFlow/Inbox ~/FileFlow/Archive
python3 app.py "${1:-5050}"
