#!/bin/bash

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "$DIR/venv/bin/activate"

# Ensure DISPLAY is set for GUI
export DISPLAY=:0

# Ensure accessibility permissions for mouse control
if [ "$(uname)" == "Darwin" ]; then
    # On macOS, check if we have accessibility permissions
    echo "Checking accessibility permissions..."
    if ! tccutil status Accessibility 2>/dev/null | grep -q "$DIR/venv/bin/python"; then
        echo "Please grant accessibility permissions when prompted"
        echo "System Preferences > Security & Privacy > Privacy > Accessibility"
        echo "Add and enable Terminal/iTerm2"
    fi
fi

# Start the bot with increased verbosity
echo "Starting ClickBot..."
"$DIR/venv/bin/python" "$DIR/cursor_auto_accept.py" > "$DIR/cursor_bot.log" 2>&1 &

# Save PID
echo $! > "$DIR/clickbot.pid"
echo "ClickBot started. To stop it, run: ./stop_clickbot.sh" 