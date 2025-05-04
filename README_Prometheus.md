# Cursor Auto Accept: Intelligent AI Code Suggestion Automation Tool

## Project Overview

Cursor Auto Accept is an intelligent automation tool designed to streamline the interaction with Cursor's AI code suggestion interface. This sophisticated bot automatically detects and clicks the "Accept" button for AI-generated code suggestions across multiple monitors, reducing manual intervention and improving developer workflow.

### Core Purpose

The primary goal of Cursor Auto Accept is to eliminate repetitive mouse clicks when accepting AI-generated code suggestions. By using advanced image recognition and template matching techniques, the tool:
- Automatically identifies Cursor's AI suggestion accept buttons
- Performs precise, context-aware clicks
- Supports multi-monitor environments
- Implements intelligent error handling and recovery mechanisms

### Key Features

#### Intelligent Matching
- Advanced template matching with configurable confidence thresholds
- Adaptive screen scanning across multiple monitors
- Precise button detection using computer vision techniques

#### Smart Interaction Controls
- Rate limiting to prevent excessive clicking (max 8 clicks per minute)
- Automatic cursor position restoration after interactions
- Comprehensive logging and debug capabilities

#### Robust Error Handling
- Automatic detection and recovery from unexpected UI states
- Graceful error logging and system monitoring
- Configurable scan intervals and debug modes

### Benefits

- **Increased Productivity**: Automates repetitive accept button clicks
- **Cross-Platform Compatibility**: Works with multiple monitor setups
- **Flexible Configuration**: Customizable confidence thresholds and scan intervals
- **Minimal Overhead**: Lightweight Python implementation with low system impact
- **Comprehensive Logging**: Detailed tracking of bot activities for transparency and troubleshooting

## Getting Started, Installation, and Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Terminal or command line interface

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cursor-auto-accept.git
cd cursor-auto-accept
```

2. Run the setup script to prepare your environment:
```bash
./setup.sh
```

### Dependencies

Install the following Python packages (automatically handled by `setup.sh`):
- OpenCV (>=4.8.0)
- NumPy (>=1.24.0)
- PyAutoGUI (>=0.9.54)
- Pillow (>=10.0.0)
- MSS (>=9.0.1)

### Calibration

Before first use, calibrate the bot for each monitor:

1. Stop any existing bot instances:
```bash
./stop_clickbot.sh
```

2. Run calibration:
```bash
# For all monitors
python cursor_auto_accept.py --capture

# For a specific monitor (0-based index)
python cursor_auto_accept.py --capture --monitor 0
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

### Development Mode

To run the bot in a development environment:
```bash
source venv/bin/activate
python cursor_auto_accept.py
```

### Monitoring

Monitor bot activity via logs:
```bash
tail -f temp/logs/clickbot.log
```

### Platform Support
- Supports Linux and macOS
- Requires Python 3.8+
- Multi-monitor configuration supported

### Important Notes
- Rate limited to 8 clicks per minute
- 80% confidence threshold for button detection
- Per-monitor calibration required

## Features / Capabilities

### Core Functionality
- Automatic AI suggestion acceptance for Cursor IDE
- Intelligent image matching for locating accept buttons
- Cross-platform support with multi-monitor configuration

### Advanced Image Recognition
- Template matching with configurable confidence thresholds
- Multi-stage image quality assessment including:
  - Structural similarity
  - Pattern confidence
  - Edge similarity
  - Histogram matching

### Performance and Reliability Features
- Rate limiting to prevent excessive clicking (max 8 clicks per minute)
- Adaptive error handling with consecutive failure detection
- Automatic cursor position restoration after clicks
- Detailed logging for tracking bot activities

### Monitor and Display Support
- Per-monitor calibration
- Dynamic screen capture across multiple displays
- Adjustable monitor-specific settings

### Safety and Control Mechanisms
- PyAutoGUI fail-safe option to stop bot by moving mouse to screen corner
- Configurable click interval and delay between actions
- Precise click targeting with center-point calculation

### Monitoring and Diagnostics
- Comprehensive logging to `temp/logs/clickbot.log`
- Runtime error tracking and reporting
- Temporary file management for debugging

### Configuration Options
- Customizable matching thresholds
  - Base confidence threshold: 0.8 (80% match)
  - High-confidence clicks require > 0.9 confidence
- Configurable search and update intervals
  - Default search interval: 0.2 seconds
  - Log update interval: 5 seconds

## Usage Examples

### Basic Usage

Run the bot using Python with optional configuration parameters:

```bash
python main.py                           # Default mode
python main.py --debug                   # Enable debug logging
python main.py --interval 5.0            # Set scan interval to 5 seconds
python main.py --confidence 0.9          # Adjust confidence threshold
```

### Configuration Options

- `--debug`: Enables verbose logging and saves debug images
- `--interval`: Sets scan interval between matches (default: 3.0 seconds)
- `--confidence`: Sets minimum confidence threshold for image matching (default: 0.8)

### Running as a Background Process

For automated execution, use the provided shell scripts:

```bash
# Start the bot in the background
./start_clickbot.sh

# Stop the running bot
./stop_clickbot.sh
```

### Platform-Specific Notes

#### macOS
- Ensure Terminal/iTerm2 has accessibility permissions
- The script will open a new Terminal window when launching

#### Linux
- The script uses `xterm` or falls back to the current terminal
- Ensure `DISPLAY` is correctly set for GUI interactions

## Project Structure

The project is organized into several key directories and files that support different functionalities:

### Core Application Files
- `main.py`: Primary entry point for the application
- `clickbot.py`: Core implementation of the click automation logic
- `cursor_auto_accept.py`: Script for automatic acceptance functionality
- `error_recovery.py`: Module handling error recovery mechanisms
- `image_matcher.py`: Image matching and template detection utilities

### Configuration and Setup
- `requirements.txt`: Lists all Python package dependencies
- `setup.sh`: Script for initial project setup
- `run_bot.sh`: Shell script to launch the application
- `start_clickbot.sh`: Script to start the clickbot
- `stop_clickbot.sh`: Script to stop the clickbot
- `logging_config.py`: Configuration for logging mechanisms
- `cursor-plugin.json`: Plugin configuration file

### Test Suite
- `test_clickbot.py`: Unit tests for the main clickbot functionality
- `test_error_recovery.py`: Tests for error recovery mechanisms
- `test_matcher.py`: Tests for image matching functionality
- `test_final.py`: Comprehensive final test suite

### Assets and Resources
- `assets/`: Directory containing various image and coordinate files
  - `monitor_0/`: Contains monitor-specific button and click coordinate files
  - `backup/`: Backup copies of button and monitor-related assets
- `debug/`: Directory with debug images and correlation visualizations
- `images/`: Additional project-related images and screenshots
- `temp/`: Temporary file storage, including logs

### Documentation
- `README.md`: Main project documentation
- `README_Prometheus.md`: Additional documentation
- `cursor-instructions/`: Subdirectory with detailed instruction files
  - `features.md`
  - `github-process.md`
  - `notes.md`
  - `readme.md`
- `mvp-scope.md`: Minimum Viable Product documentation

### Utility Scripts
- `analyze_calibration.py`: Script for calibration analysis
- `analyze_hover_results.py`: Hover result analysis utility
- `analyze_template.py`: Template analysis script
- `hover_calibrate.py`: Hover calibration script

### Extension and Plugin
- `extension.js`: Potentially a browser or IDE extension script

The project structure is designed to modularize different aspects of the application, separating core logic, testing, configuration, and resource management into distinct directories and files.

## Technologies Used

### Programming Language
- Python 3

### Core Libraries and Frameworks
- OpenCV (opencv-python): Computer vision and image processing
- NumPy: Numerical computing and array operations
- Pillow (PIL): Image manipulation and processing
- PyAutoGUI: GUI automation and screen interaction

### System and Utility Libraries
- OS: Operating system interactions
- Sys: System-specific parameters and functions
- Time: Time access and conversions
- Signal: Signal handling
- Datetime: Date and time manipulation
- Argparse: Command-line argument parsing

### Monitoring and Logging
- Integrated custom logging configuration for detailed tracking and debugging

### Development Tools
- Python standard library
- Shell scripts for bot management (`.sh` files)

### Platform Support
- Cross-platform (Windows, macOS, Linux) through Python libraries

## Additional Notes

### Performance Considerations

The script is designed with rate limiting to prevent excessive system load, capped at 8 clicks per minute. This helps maintain system stability and prevents potential disruptions during AI suggestion acceptance.

### Monitoring and Logging

All bot activities are comprehensively logged in `temp/logs/clickbot.log`. The logging system provides:
- Timestamped event tracking
- Click event recordings
- Error and status updates
- Configurable log update interval (default: 5 seconds)

### Multi-Monitor Support

The bot supports calibration and operation across multiple monitors, with:
- Per-monitor button detection
- Separate calibration images for each display
- Flexible monitor selection during calibration
- Dynamic screen scanning capability

### Error Recovery

The bot includes built-in error recovery mechanisms:
- Automatic restart capabilities
- Persistent process tracking via PID files
- Graceful handling of calibration and detection failures
- Configurable confidence thresholds for button matching

### Security and Privacy

Key security features include:
- Cursor position restoration after clicks
- Rate-limited automation to prevent system abuse
- Local image-based detection (no network dependencies)
- No persistent storage of sensitive information

### System Requirements

Ensure the following Python libraries are installed:
- OpenCV for image processing
- PyAutoGUI for mouse and keyboard automation
- MSS for multi-screen screenshots
- NumPy for numerical operations
- Pillow for image handling

### Compatibility

- Tested on Python 3.8+
- Compatible with major operating systems
- Requires GUI access for mouse and keyboard control

### Limitations

- Requires manual initial calibration
- Dependent on consistent UI elements in Cursor AI
- Performance may vary with different screen resolutions and UI scaling

## Contributing

We welcome contributions to this project! To help maintain code quality and collaboration efficiency, please follow these guidelines:

### Branch Strategy
- Create a new branch for each major feature or significant change
- Branch names should initially use a timestamp, which can later be renamed to a more descriptive name

### Commit Guidelines
- Commit your work after completing a specific improvement or feature
- Push your changes to the branch after each commit
- Ensure that commits represent logical, cohesive changes

### Feature Development
- Major features should only be implemented when specifically requested
- Document new features in the project's feature documentation
- Take notes about ideas, improvements, or potential vulnerabilities in the project notes

### Testing and Debugging
- Thoroughly test all changes before submitting
- Test one feature or change at a time
- Carefully review logs and debug any encountered errors
- Prioritize security and potential vulnerabilities

### Pull Request Process
- Ensure your code follows the existing project structure and style
- Include clear, descriptive commit messages
- Be prepared to discuss and iterate on your proposed changes

### Additional Notes
- Efficiency and security are key priorities for this project
- Be prepared to provide detailed information about your proposed changes

### Questions or Suggestions
If you have questions about contributing, please open an issue to discuss your proposed changes.

## License

This project is licensed under the MIT License. 

#### Key Permissions

The MIT License is a permissive open-source license that provides the following rights:

- Commercial use
- Modification
- Distribution
- Private use
- Warranty placement

#### Conditions

The only requirement is to include the original copyright notice and permission notice in any substantial portion of the software.

For the complete license text, please refer to the [LICENSE](LICENSE) file in the repository.