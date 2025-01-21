#!/bin/bash

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if PID file exists
if [ -f "$DIR/temp/clickbot.pid" ]; then
    # Read PID and kill process
    PID=$(cat "$DIR/temp/clickbot.pid")
    if kill $PID > /dev/null 2>&1; then
        echo "ClickBot stopped (PID: $PID)"
        rm "$DIR/temp/clickbot.pid"
    else
        echo "ClickBot process not found (PID: $PID)"
        rm "$DIR/temp/clickbot.pid"
    fi
else
    echo "ClickBot PID file not found"
fi 