#!/bin/bash
# Quick start — runs FileFlow in the foreground
# For background mode, use: fileflow start
cd "$(dirname "$0")"
pip3 install -q -r "$(dirname "$0")/requirements.txt" 2>/dev/null
mkdir -p ~/FileFlow/Inbox ~/FileFlow/Archive
python3 app.py "${1:-5050}"
