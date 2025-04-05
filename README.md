# Cursor Auto Accept

An intelligent bot for automatically accepting Cursor AI suggestions across multiple monitors.

## Project Overview

Cursor Auto Accept is an automated tool designed to streamline the workflow of developers using Cursor AI by automatically detecting and clicking the "Accept" button for AI-generated code suggestions. This bot supports multi-monitor setups, provides detailed logging, and includes advanced features like rate limiting and error recovery.

## Features

- 🖥️ Multi-monitor support
- 🤖 Automatic AI suggestion acceptance
- 📍 Precise button detection using template matching
- 🔒 Rate limiting (max 8 clicks per minute)
- 🔍 High-confidence matching (80% threshold)
- 📊 Comprehensive logging and monitoring
- 🛡️ Error recovery mechanisms
- 🖱️ Cursor position restoration after clicks

## Technologies Used

- **Language**: Python 3.8+
- **Libraries**:
  - OpenCV (image processing)
  - PyAutoGUI (GUI automation)
  - MSS (Multi-Screen Screenshot)
  - NumPy (numerical computing)
  - Pillow (image handling)

## Prerequisites

- Python 3.8 or higher
- Git
- Access to a terminal/command line

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
   - Set up permissions
   - Create a Python virtual environment
   - Install required dependencies

### Calibration

Before first use, calibrate the bot for each monitor:

1. Stop any running bot instances:
   ```bash
   ./stop_clickbot.sh
   ```

2. Run calibration:
   ```bash
   # Calibrate all monitors
   python cursor_auto_accept.py --capture

   # Or calibrate a specific monitor
   python cursor_auto_accept.py --capture --monitor 0
   ```

3. Follow on-screen instructions:
   - Move Cursor to the target monitor
   - Trigger an AI prompt
   - Move mouse over the accept button
   - Keep mouse still for 5 seconds
   - Wait for confirmation

### Usage

Start the bot:
```bash
./start_clickbot.sh
```

Stop the bot:
```bash
./stop_clickbot.sh
```

Monitor logs:
```bash
tail -f temp/logs/clickbot.log
```

## Project Structure

```
.
├── assets/               # Calibration images per monitor
├── debug/                # Debug and diagnostic images
├── temp/                 # Runtime files and logs
├── cursor_auto_accept.py # Main bot script
├── setup.sh              # Environment setup script
├── start_clickbot.sh     # Bot start script
└── stop_clickbot.sh      # Bot stop script
```

## Configuration

Configurable settings include:
- Rate limit: 8 clicks per minute
- Confidence threshold: 0.8 (80% match)
- Search interval: 0.2 seconds
- Log update interval: 5 seconds

## Troubleshooting

- Check logs for specific error details
- Recalibrate monitors with unclear button detection
- Ensure no other bot instances are running
- Verify Python environment activation

## Contributing

Contributions are welcome! Please read the contributing guidelines and submit pull requests to the main repository.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Disclaimer

Use this tool responsibly and in compliance with Cursor's terms of service. The tool is meant to enhance productivity, not to abuse AI generation.