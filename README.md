# Cursor Auto Accept CLI

## Project Overview

Cursor Auto Accept is a powerful command-line interface (CLI) tool designed to automate the acceptance of AI suggestions in the Cursor IDE. This tool helps developers streamline their workflow by automatically clicking the "Accept" button for AI-generated code suggestions across multiple monitors.

Key features include:
- Multi-monitor support
- Automatic button detection and clicking
- Configurable rate limiting
- Detailed logging and error handling
- Adaptive calibration mechanism

### Use Cases
- Quickly accept multiple AI code suggestions
- Reduce manual repetitive tasks during AI-assisted coding
- Support developers working across multiple screens

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Install via pip
```bash
pip install cursor-auto-accept
```

### Manual Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/cursor-auto-accept.git
cd cursor-auto-accept

# Run setup script
./setup.sh
```

## Usage

### Basic Commands

1. Start the Auto Accept Bot
```bash
# Start bot for all monitors
./start_clickbot.sh

# Start bot for a specific monitor
python cursor_auto_accept.py --monitor 0
```

2. Stop the Bot
```bash
./stop_clickbot.sh
```

3. Calibration Mode
```bash
# Calibrate all monitors
python cursor_auto_accept.py --capture

# Calibrate a specific monitor
python cursor_auto_accept.py --capture --monitor 1
```

### Advanced Usage

#### Monitor-Specific Options
```bash
# Specify confidence threshold
python cursor_auto_accept.py --confidence 0.85

# Set custom click rate limit
python cursor_auto_accept.py --rate-limit 10
```

## Command Reference

| Command               | Description                            | Options                      |
|----------------------|----------------------------------------|-----------------------------|
| `--capture`          | Enter calibration mode                 | `--monitor` (optional)      |
| `--monitor`          | Select specific monitor for operation  | Integer (0-based index)     |
| `--confidence`       | Set template matching confidence       | Float (0-1, default: 0.8)   |
| `--rate-limit`       | Set maximum clicks per minute          | Integer (default: 8)        |

## Configuration

### Monitor Calibration
Calibration images are stored in `assets/monitor_X/accept_button.png` for each monitor.

### Configuration File
Create a `cursor_auto_accept.json` in your home directory:
```json
{
    "monitors": [0, 1, 2],
    "confidence_threshold": 0.8,
    "max_clicks_per_minute": 8,
    "log_level": "INFO"
}
```

## Project Structure

```
.
├── assets/             # Monitor-specific calibration images
├── temp/               # Runtime and log files
│   └── logs/
├── cursor_auto_accept.py  # Main CLI script
├── setup.sh            # Installation script
├── start_clickbot.sh   # Bot start script
└── stop_clickbot.sh    # Bot stop script
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

Please ensure:
- All tests pass (`python -m pytest`)
- Code follows PEP 8 guidelines
- Add/update tests for new features

## Requirements

- Python 3.8+
- OpenCV
- PyAutoGUI
- MSS
- NumPy
- Pillow

## Troubleshooting

- Check `temp/logs/clickbot.log` for detailed logs
- Ensure Python virtual environment is activated
- Recalibrate monitors if button detection fails

## License

MIT License. See `LICENSE` file for details.