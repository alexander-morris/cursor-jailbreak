#!/bin/bash

# Directory setup
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Run setup if needed
if [ ! -d "./temp" ]; then
    echo "Initializing directory structure..."
    ./setup.sh
fi

# Check if already running
if [ -f "./temp/clickbot.pid" ]; then
    PID=$(cat "./temp/clickbot.pid")
    if ps -p $PID > /dev/null 2>&1; then
        echo "ClickBot is already running with PID $PID"
        exit 1
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Start the bot
echo "Starting ClickBot..."
python cursor_auto_accept.py &
PID=$!
echo $PID > "./temp/clickbot.pid"
echo "ClickBot started. To stop it, run: ./stop_clickbot.sh" 