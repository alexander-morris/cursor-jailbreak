# Cursor Auto-Continue Bot

An automated tool for detecting and handling various Cursor AI interaction scenarios, including note detection and handling stuck conversations.

## Features

- Multi-monitor support with automatic window tracking
- Automatic target detection and clicking across all monitors
- Automatic note detection and response
- Stuck conversation detection and recovery
- Smart prompt interaction with visual verification
- Development mode for testing
- Robust error handling and detailed logging

## Requirements

- Python 3.x
- OpenCV
- numpy
- pyautogui
- mss (Multi-Screen Shot)
- Pillow

## Installation

1. Clone the repository:
```bash
git clone [your-repo-url]
cd cursor-auto-continue
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Place required images in the `images` directory:
- `note-with-icon.png` - Note icon image
- `note-text.png` - Note text image
- `composer-title.png` - Composer window title image
- `target.png` - Target button image (created during calibration)

## Usage

### Initial Setup
First, calibrate the target button detection:
```bash
python cursor_auto_accept.py --calibrate
```
When prompted, move your cursor to the center of a target button and press Enter.

### Production Mode
Run the bot in normal mode with standard timeouts:
```bash
python cursor_auto_accept.py
```

### Development Mode
Run with shortened timeouts for testing:
```bash
python cursor_auto_accept.py --dev
```

### Test Modes
Test specific functionality:
```bash
python cursor_auto_accept.py --test-target  # Test target detection
python cursor_auto_accept.py --test-note    # Test note detection
python cursor_auto_accept.py --test-stuck   # Test stuck detection
```

### Timeouts and Settings

Production Mode:
- Stuck detection: 70 seconds
- Stuck handler cooldown: 5 minutes
- Action cooldown: 2 seconds

Development Mode:
- Stuck detection: 10 seconds
- No stuck handler cooldown
- Action cooldown: 2 seconds

## Features in Detail

### Target Detection
- Continuously scans all monitors for target buttons
- Handles multiple targets across different monitors
- Clicks targets in top-to-bottom order
- Includes visual verification of successful clicks
- Automatic retry on failed clicks

### Note Detection
- Continuously monitors all screens for note icons
- Automatically types "continue" when a note is detected
- Includes click verification and retry logic

### Stuck Detection
- Monitors the composer view for changes
- Detects when conversation has been inactive
- Sends reminder message with instructions
- Tracks window movement to maintain accuracy

### Window Tracking
- Updates composer window position every second
- Handles window movement across monitors
- Logs significant position changes
- Gracefully handles lost window scenarios

## Logging

The bot logs all activities to:
- Console output (real-time)
- `cursor_bot.log` file

Log includes:
- Monitor detection and configuration
- Target detection and click attempts
- Window position changes
- Click attempts and verifications
- Error conditions and recovery attempts
- Stuck detection and handling

## Error Handling

- Visual verification of clicks
- Automatic retry on failed clicks
- Graceful handling of lost windows
- Exception catching and logging
- Monitor boundary checking

## Development

### Running Tests
Use test modes for specific functionality:
```bash
python cursor_auto_accept.py --test-target  # Test target detection
python cursor_auto_accept.py --test-note    # Test note detection
python cursor_auto_accept.py --test-stuck   # Test stuck detection
```

### Adding Features
1. Create a new feature branch
2. Implement changes
3. Test in development mode
4. Submit pull request

## Troubleshooting

1. If target detection isn't working:
   - Run calibration again with `--calibrate`
   - Ensure target button is clearly visible
   - Check monitor configuration
   - Review logs for detection attempts

2. If clicks aren't registering:
   - Check monitor configuration
   - Verify prompt field position
   - Adjust click verification threshold

3. If stuck detection isn't working:
   - Verify composer window is visible
   - Check `composer-title.png` matches
   - Review logs for position tracking

4. If note detection fails:
   - Verify note images are correct
   - Check confidence threshold
   - Ensure proper monitor coverage

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details 