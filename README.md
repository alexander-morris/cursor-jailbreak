# ClickBot: Automated UI Interaction CLI Tool

## Project Overview

ClickBot is an intelligent, configurable CLI tool designed for automated UI interaction and screen-based task automation. Using advanced image matching and error recovery techniques, ClickBot can automatically detect and interact with specific UI elements across multiple monitors.

### Key Features
- 🖥️ Multi-monitor support
- 🎯 Configurable confidence threshold for UI element matching
- 🐛 Built-in error recovery mechanisms
- 📊 Flexible scanning intervals
- 🔍 Optional debug mode for detailed logging

### Use Cases
- Automating repetitive UI interactions
- Testing UI workflows
- Handling monotonous screen-based tasks
- Simulating user interactions for testing or productivity

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Dependencies
- opencv-python (>=4.8.0)
- numpy (>=1.24.0)
- pyautogui (>=0.9.54)
- pillow (>=10.0.0)
- mss (>=9.0.1)

### Install Steps
1. Clone the repository:
```bash
git clone https://github.com/yourusername/clickbot.git
cd clickbot
```

2. Create a virtual environment (optional but recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Command
```bash
python main.py
```

### Command Line Options
```bash
python main.py [OPTIONS]
```

#### Options
- `--debug`: Enable verbose debug logging
- `--interval FLOAT`: Set scan interval in seconds (default: 3.0)
- `--confidence FLOAT`: Set minimum confidence threshold for matches (default: 0.8)

### Example Commands
1. Run with default settings:
```bash
python main.py
```

2. Run in debug mode with custom interval:
```bash
python main.py --debug --interval 5.0
```

3. Adjust confidence threshold:
```bash
python main.py --confidence 0.75
```

## Command Reference

| Option        | Type    | Default | Description                                   |
|---------------|---------|---------|-----------------------------------------------|
| `--debug`     | Flag    | False   | Enable detailed debug logging                 |
| `--interval`  | Float   | 3.0     | Seconds between screen scans                  |
| `--confidence`| Float   | 0.8     | Minimum match confidence (0.0 - 1.0)          |

## Project Structure
- `main.py`: Primary executable script
- `image_matcher.py`: Image matching and screen capture logic
- `error_recovery.py`: Error detection and recovery mechanisms
- `logging_config.py`: Logging configuration
- `requirements.txt`: Project dependencies
- `assets/`: Image resources for UI matching

## Configuration

### Logging
- Log files are automatically generated in the project directory
- Debug mode provides more verbose logging details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Testing
Run tests using:
```bash
python -m unittest discover
```

## Limitations & Considerations
- Requires visual UI elements for matching
- Performance depends on screen resolution and UI complexity
- Works best with stable, predictable UI layouts

## License
[Specify your license, e.g., MIT License]

## Support
For issues or feature requests, please file a GitHub issue in the repository.