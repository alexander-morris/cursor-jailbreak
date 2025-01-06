# Cursor Auto Accept

A tool for automatically accepting Cursor's AI suggestions.

## Important Note

The `analyze_hover_results.py` script is the current working version for analyzing button positions and matches. This script:
- Takes a full screen screenshot
- Analyzes potential button matches using template matching
- Groups matches by x-axis position
- Prioritizes matches by confidence and y-axis position
- Generates a visualization showing calibration points and matches
- Uses color coding to distinguish between different buttons (green, yellow, red)

Other calibration scripts have been moved to the `_archive` directory.

## Features

- Multi-monitor support with per-monitor calibration
- Rate limiting (max 8 clicks per minute)
- Cursor position restoration after clicks
- Automatic calibration
- Process management (start/stop scripts)
- Detailed logging

## Setup

1. Clone this repository:
```bash
git clone https://github.com/yourusername/cursor-auto-accept
cd cursor-auto-accept
```

2. Run the setup script:
```bash
./setup.sh
```
This will:
- Create necessary directories
- Set up permissions
- Create a Python virtual environment
- Install required packages

## Calibration

Before first use, you need to calibrate the bot for each monitor where you use Cursor:

1. Stop the bot if it's running:
```bash
./stop_clickbot.sh
```

2. Run calibration mode:

   For all monitors:
   ```bash
   source venv/bin/activate
   python cursor_auto_accept.py --capture
   ```

   For a specific monitor (0-based index):
   ```bash
   python cursor_auto_accept.py --capture --monitor 0  # First monitor
   python cursor_auto_accept.py --capture --monitor 1  # Second monitor
   ```

3. Follow the calibration steps for each monitor:
   - Move Cursor to the target monitor
   - Trigger an AI prompt (so you can see the accept button)
   - Move your mouse over the accept button
   - Keep it still for 5 seconds
   - Wait for confirmation message
   - Press Enter to continue to next monitor (if calibrating all)

The bot will save separate accept button images for each monitor in:
```
assets/monitor_0/accept_button.png
assets/monitor_1/accept_button.png
...
```

## Usage

### Starting the Bot

```bash
./start_clickbot.sh
```

The bot will:
- Check if another instance is running
- Load calibration images for all monitors
- Start monitoring all screens
- Begin accepting prompts automatically

### Stopping the Bot

```bash
./stop_clickbot.sh
```

### Monitoring

The bot logs all activity to `temp/logs/clickbot.log`. You can monitor it with:
```bash
tail -f temp/logs/clickbot.log
```

## Configuration

The bot has several built-in settings:
- Rate limit: 8 clicks per minute
- Confidence threshold: 0.8 (80% match required)
- Search interval: 0.2 seconds
- Log update interval: 5 seconds

## Troubleshooting

1. If the bot isn't clicking on a specific monitor:
   - Recalibrate that monitor: `python cursor_auto_accept.py --capture --monitor X`
   - Check the logs for monitor-specific errors
   - Ensure Cursor's accept button is visible on that monitor

2. If clicks are inaccurate:
   - Recalibrate with a clearer view of the accept button
   - Make sure the button isn't partially obscured
   - Try calibrating in different lighting conditions

3. If the bot won't start:
   - Check if another instance is running
   - Verify the PID file in `temp/clickbot.pid`
   - Ensure Python environment is activated

## Directory Structure

```
.
├── assets/                    # Calibration images
│   ├── monitor_0/            # First monitor
│   │   └── accept_button.png
│   └── monitor_1/            # Second monitor
│       └── accept_button.png
├── temp/                     # Runtime files
│   ├── clickbot.pid          # Process ID
│   └── logs/                # Log files
├── cursor_auto_accept.py     # Main bot script
├── setup.sh                  # Setup script
├── start_clickbot.sh         # Start script
└── stop_clickbot.sh          # Stop script
```

## Requirements

- Python 3.8+
- OpenCV
- PyAutoGUI
- MSS (Multi-Screen Shot)
- NumPy
- Pillow

## License

MIT License 