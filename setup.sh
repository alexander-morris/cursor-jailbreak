#!/bin/bash

# Create required directories
mkdir -p ./temp
mkdir -p ./temp/logs
mkdir -p ./images
mkdir -p ./assets

# Set up permissions
chmod -R 755 ./temp
chmod -R 755 ./images
chmod -R 755 ./assets

# Create empty files if they don't exist
touch ./temp/clickbot.pid
touch ./temp/logs/clickbot.log

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment and install requirements
source venv/bin/activate
pip install -r requirements.txt

echo "ClickBot directory structure initialized" 