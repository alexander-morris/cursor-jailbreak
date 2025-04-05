# Cursor Auto Accept CLI

## Project Overview

Cursor Auto Accept is an intelligent CLI tool designed to automatically accept AI code suggestions in the Cursor IDE across multiple monitors. This automation tool helps developers maintain workflow efficiency by reducing manual interactions with AI-generated code suggestions.

Key benefits:
- Minimize context switching during coding
- Automate repetitive UI interactions
- Support multi-monitor development environments
- Provide detailed logging and monitoring

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Installation Methods

#### 1. Direct Git Clone
```bash
git clone https://github.com/yourusername/cursor-auto-accept.git
cd cursor-auto-accept
```

#### 2. Setup Script
```bash
./setup.sh
```

This script will:
- Create Python virtual environment
- Install dependencies
- Set up necessary directories

### Dependencies
- OpenCV
- PyAutoGUI
- MSS (Multi-Screen Shot)
- NumPy
- Pillow

## Usage

### Starting the Bot
```bash
# Start the auto-accept bot
./start_clickbot.sh
```

### Stopping the Bot
```bash
# Stop the running bot
./stop_clickbot.sh
```

### Calibration
Before first use, calibrate the bot for each monitor:

```bash
# Calibrate all monitors
python cursor_auto_accept.py --capture

# Calibrate specific monitor (0-based index)
python cursor_auto_accept.py --capture --monitor 0
python cursor_auto_accept.py --capture --monitor 1
```

### Monitoring Logs
```bash
# Real-time log monitoring
tail -f temp/logs/clickbot.log
```

## Command Reference

| Command | Flags | Description | Example |
|---------|-------|-------------|---------|
| `cursor_auto_accept.py` | `--capture` | Start calibration mode | `python cursor_auto_accept.py --capture` |
| `cursor_auto_accept.py` | `--monitor` | Specify monitor for calibration | `python cursor_auto_accept.py --capture --monitor 1` |
| `start_clickbot.sh` | - | Start auto-accept bot | `./start_clickbot.sh` |
| `stop_clickbot.sh` | - | Stop auto-accept bot | `./stop_clickbot.sh` |

## Configuration

### Default Settings
- Rate limit: 8 clicks per minute
- Confidence threshold: 0.8 (80% match)
- Search interval: 0.2 seconds
- Log update interval: 5 seconds

### Configuration Location
Configuration is managed via script defaults and command-line flags.

## Project Structure
```
.
├── assets/               # Monitor-specific calibration images
├── temp/                 # Runtime files and logs
│   ├── clickbot.pid
│   └── logs/
├── cursor_auto_accept.py # Main bot script
├── setup.sh              # Environment setup
└── start_clickbot.sh     # Bot management scripts
```

## Troubleshooting

### Common Issues
1. Bot not clicking on specific monitor
   - Recalibrate the monitor
   - Check logs for specific errors
   - Ensure Cursor's accept button is visible

2. Inaccurate clicks
   - Recalibrate with a clear button view
   - Avoid partially obscured buttons
   - Calibrate in consistent lighting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

Please include:
- Clear description of changes
- Updated tests
- Documentation updates

## License

MIT License. See LICENSE file for details.

## Contact

For issues, feature requests, or support, please [open an issue](https://github.com/yourusername/cursor-auto-accept/issues).