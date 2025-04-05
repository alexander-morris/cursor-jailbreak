# Cursor Auto Accept Bot

## Project Overview

Cursor Auto Accept is an intelligent automation tool designed to automatically accept AI suggestions in the Cursor IDE. The bot enhances developer productivity by automatically clicking "Accept" buttons across multiple monitors, with advanced image recognition and calibration capabilities.

## Key Features

- 🖥️ Multi-monitor support
- 🎯 Precise template matching with computer vision
- 🤖 Automated AI suggestion acceptance
- 🔍 Configurable confidence thresholds
- 📊 Rate-limited interactions (max 8 clicks per minute)
- 🔧 Robust error handling and logging
- 🌐 Cross-platform compatibility

## Technologies Used

- **Programming Language**: Python 3.8+
- **Computer Vision**: OpenCV
- **Image Processing**: 
  - PyAutoGUI
  - MSS (Multi-Screen Shot)
  - NumPy
  - Pillow
- **Platform**: Cross-platform (Windows, macOS, Linux)

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Cursor IDE installed

## Getting Started

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cursor-auto-accept.git
cd cursor-auto-accept
```

2. Run the setup script:
```bash
./setup.sh
```

This script will:
- Create necessary directories
- Set up Python virtual environment
- Install required dependencies

### Calibration

Before first use, calibrate the bot for each monitor:

1. Stop any running bot instances:
```bash
./stop_clickbot.sh
```

2. Start calibration:
```bash
# Calibrate all monitors
python cursor_auto_accept.py --capture

# Or calibrate a specific monitor
python cursor_auto_accept.py --capture --monitor 0
```

Follow on-screen instructions:
- Move Cursor to the target monitor
- Trigger an AI prompt
- Position mouse over the accept button
- Keep mouse still for 5 seconds
- Confirm calibration

## Usage

### Starting the Bot

```bash
./start_clickbot.sh
```

### Stopping the Bot

```bash
./stop_clickbot.sh
```

### Monitoring Logs

```bash
tail -f temp/logs/clickbot.log
```

## Configuration Parameters

- **Rate Limit**: 8 clicks per minute
- **Confidence Threshold**: 0.8 (80% match required)
- **Search Interval**: 0.2 seconds
- **Log Update Interval**: 5 seconds

## Project Structure

```
cursor-auto-accept/
├── assets/               # Monitor-specific calibration images
├── temp/                 # Runtime files and logs
├── cursor_auto_accept.py # Main bot script
├── setup.sh              # Environment setup script
├── start_clickbot.sh     # Bot start script
└── stop_clickbot.sh      # Bot stop script
```

## Troubleshooting

- Check logs for specific error details
- Recalibrate monitors if clicks are inaccurate
- Ensure Python virtual environment is activated
- Verify no conflicting bot instances are running

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is provided "as is" without warranty. Use responsibly and in compliance with Cursor's terms of service.