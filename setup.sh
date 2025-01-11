#!/bin/bash

# Create necessary directories
mkdir -p images temp/logs

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

echo "Setup complete! Virtual environment created and dependencies installed."
echo "Don't forget to place your image files in the images/ directory:"
echo "- note-with-icon.png"
echo "- note-text.png"
echo "- composer-title.png" 