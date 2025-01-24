# HustleBot Clicker

An automated UI interaction tool with two implementations:
1. `main.py` - Full-featured bot with multi-monitor support and advanced error recovery
2. `basic_clicker.py` - Simplified single-monitor implementation with calibration

## Project Structure
```
.
├── main.py              # Primary implementation
├── basic_clicker.py     # Secondary implementation
├── src/                 # Core dependencies
│   ├── image_matcher.py     # OpenCV-based image matching
│   ├── error_recovery.py    # Error handling and recovery
│   └── logging_config.py    # Logging configuration
├── images/              # Reference images directory
├── requirements.txt     # Python dependencies
└── README.md           # Documentation
```

## Installation

1. Install system dependencies (Linux):
```bash
sudo apt-get install python3-tk python3-dev
```
If these packages are already installed, you'll see a message like:
```
python3-tk is already the newest version
python3-dev is already the newest version
```

2. Create and activate a Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```
Your prompt should change to show `(venv)` at the beginning, indicating the virtual environment is active.

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```
You should see several packages being downloaded and installed, including `opencv-python`, `numpy`, `pyautogui`, and others. The installation is successful when you see "Successfully installed..." followed by a list of packages.

4. Set up reference images:
   - Create an `images` directory if it doesn't exist
   - For `main.py`: Add `cursor-screen-head.png` (screenshot of Cursor window header)
   - For `basic_clicker.py`: No reference images needed (uses calibration)

To verify the setup was successful, run:
```bash
python3 basic_clicker.py --calibrate
```
You should see:
```
Running calibration...

Currently have 0 targets.

=== Button Present Calibration ===
Target #1
1. Hover over the target button when it IS present (DO NOT CLICK)...
```
If you see this output, the setup is complete and you can proceed with calibration.

## Quick Start (Linux)

A convenience script is provided to handle all setup and verification:

1. First time setup with calibration:
```bash
./start-clicker.sh --calibrate
```

2. Normal operation (after calibration):
```bash
./start-clicker.sh
```

The script will:
- Check for required system packages
- Create and activate virtual environment if needed
- Install Python dependencies if missing
- Create images directory if it doesn't exist
- Run the clicker in the specified mode

Each step will show a ✓ when successful or ✗ with an error message if something needs attention.

## Basic Clicker (basic_clicker.py)

A simplified implementation with built-in calibration.

### Features
- Interactive calibration process
- Multiple target support
- Consecutive match verification
- Returns cursor to original position after clicks
- Development mode with timeout
- Click verification with screenshots
- Session statistics (clicks/hour, success rate)
- Improved error handling
- Reduced debug output verbosity

### Usage

1. **Calibration Mode**:
```bash
python basic_clicker.py --calibrate
```

During calibration:
1. For each target you want to click:
   - When prompted, hover (don't click) over the button when it's visible
   - Press Enter
   - Wait for the button to disappear completely
   - Press Enter again
2. Repeat for additional targets
3. Type 'y' when done adding targets

2. **Normal Operation**:
```bash
python basic_clicker.py
```

3. **Development Mode** (30-second timeout):
```bash
python basic_clicker.py --dev
```

### Configuration
- Minimum click interval: 5.0 seconds
- Required consecutive matches: 2
- Similarity threshold: 0.65
- Match verification weight: 70% pixel difference, 30% exact matches
- Click verification threshold: 10 (mean pixel difference)
- Debug output threshold: 0.8 (similarity score)

### Session Statistics
The bot tracks and displays:
- Total runtime in hours
- Total clicks attempted
- Successful clicks (verified)
- Clicks per hour
- Success rate percentage

Statistics are displayed every 10 clicks and at shutdown.

## Main Bot (main.py)

The full-featured implementation with advanced capabilities.

### Features
- Multi-monitor support
- Automatic window detection
- Advanced error recovery
- Resource cleanup
- Configurable cache clearing

### Usage

1. **Debug Mode** (recommended for first run):
```bash
python main.py --debug
```

2. **Custom Configuration**:
```bash
python main.py --interval 2.0 --confidence 0.8
```

### Command Line Options
```bash
python main.py [options]
  --debug            Enable debug logging
  --interval FLOAT   Scan interval in seconds (default: 3.0)
  --confidence FLOAT Confidence threshold (default: 0.8)
```

## Configuration Tips

### Confidence Threshold
- Start with default (0.8)
- Increase if getting false positives
- Decrease if missing valid targets
- Recommended ranges:
  - High accuracy: 0.8-0.9
  - Normal use: 0.7-0.8
  - Lenient: 0.6-0.7

### Scan Interval
- Default: 3.0 seconds
- Decrease for faster response
- Increase to reduce CPU usage
- Recommended ranges:
  - Fast response: 1.0-2.0
  - Normal use: 2.0-4.0
  - Low CPU: 4.0+

## Troubleshooting

### Basic Clicker Issues
1. **Calibration Problems**
   - Ensure clear button visibility during "present" state
   - Ensure complete button absence during "absent" state
   - Check mean difference values (should be > 5)
   - Verify click success with UI state changes

2. **False Positives/Negatives**
   - Increase consecutive match requirement
   - Adjust similarity threshold
   - Recalibrate with more distinct states
   - Monitor click verification results

### Main Bot Issues
1. **Window Detection**
   - Run with --debug flag
   - Check monitor configuration
   - Verify window visibility

2. **Click Accuracy**
   - Increase confidence threshold
   - Check for window movement
   - Verify target coordinates

## Best Practices

1. **Target Selection**
   - Choose distinct, stable UI elements
   - Avoid areas with dynamic content
   - Calibrate during normal operation conditions

2. **Performance**
   - Balance interval vs CPU usage
   - Monitor memory usage
   - Clean logs periodically

3. **Testing**
   - Always test in safe environments
   - Use development mode for initial setup
   - Monitor logs during operation

## License

MIT License - Feel free to modify and distribute 