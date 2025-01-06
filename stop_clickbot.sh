#!/bin/bash

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if PID file exists
if [ -f "$DIR/clickbot.pid" ]; then
    PID=$(cat "$DIR/clickbot.pid")
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        rm "$DIR/clickbot.pid"
        echo "ClickBot stopped"
    else
        echo "ClickBot process not found (PID: $PID)"
        rm "$DIR/clickbot.pid"
    fi
else
    echo "ClickBot PID file not found"
fi 