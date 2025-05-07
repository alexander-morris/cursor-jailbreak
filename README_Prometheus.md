# Prometheus: Add README for cursor-jailbreak

## Project Overview

Cursor Auto Accept is an intelligent automation tool designed to streamline the process of accepting AI suggestions in the Cursor development environment. The tool addresses the repetitive task of manually clicking "Accept" buttons for AI-generated code suggestions across multiple monitors.

### Key Features

- **Automatic AI Suggestion Acceptance**: Automatically detects and clicks "Accept" buttons for Cursor AI suggestions
- **Multi-Monitor Support**: Calibrates and operates seamlessly across different monitor setups
- **Intelligent Button Detection**: Uses advanced template matching with computer vision techniques
- **Robust Performance Controls**:
  - Rate limiting to prevent excessive clicks (maximum 8 clicks per minute)
  - Cursor position restoration after interactions
  - Automatic calibration process
  - Detailed logging for tracking bot activities

### Problem Solved

Developers using Cursor AI often face the repetitive task of manually accepting code suggestions. This tool eliminates this manual intervention, allowing developers to maintain their workflow focus while benefiting from AI-assisted coding suggestions. By automating the acceptance process, it reduces cognitive load and potential interruptions during coding sessions.

## Getting Started, Installation, and Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Basic command-line interface knowledge

### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cursor-auto-accept.git
cd cursor-auto-accept
```

2. Run the setup script to prepare the environment:
```bash
./setup.sh
```
This script will:
- Create necessary directories
- Set up file permissions
- Create a Python virtual environment
- Install all required dependencies

### Dependencies

The project requires the following Python libraries (automatically installed via setup):
- OpenCV
- PyAutoGUI
- MSS (Multi-Screen Shot)
- NumPy
- Pillow

### Configuration and Calibration

Before using the bot, you must calibrate it for each monitor:

1. Ensure the bot is stopped:
```bash
./stop_clickbot.sh
```

2. Calibrate for all monitors:
```bash
source venv/bin/activate
python cursor_auto_accept.py --capture
```

Or calibrate a specific monitor:
```bash
python cursor_auto_accept.py --capture --monitor 0  # First monitor
python cursor_auto_accept.py --capture --monitor 1  # Second monitor
```

### Running the Bot

Start the bot:
```bash
./start_clickbot.sh
```

Stop the bot:
```bash
./stop_clickbot.sh
```

### Logging and Monitoring

Monitor bot activity by checking the log file:
```bash
tail -f temp/logs/clickbot.log
```

### Quick Start

1. Complete installation steps
2. Calibrate for your monitors
3. Start the bot
4. The bot will automatically accept Cursor AI suggestions across configured monitors

### Notes

- The bot is rate-limited to 8 clicks per minute
- Calibration images are saved per monitor in the `assets/monitor_X/` directories
- Ensure Cursor's accept button is clearly visible during calibration