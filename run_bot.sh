#!/bin/bash

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Set Python to unbuffered mode
export PYTHONUNBUFFERED=1

# Check if we're on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Open a new terminal window and run the bot
    osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'\" && PYTHONUNBUFFERED=1 python3 -u main.py"'
else
    # For other systems, try to use xterm
    if command -v xterm >/dev/null 2>&1; then
        xterm -e "cd \"$(pwd)\" && PYTHONUNBUFFERED=1 python3 -u main.py"
    else
        # Fallback to running in current terminal
        PYTHONUNBUFFERED=1 python3 -u main.py
    fi
fi 