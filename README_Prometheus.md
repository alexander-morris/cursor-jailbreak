# Cursor Auto Accept: An Intelligent UI Interaction Automation Tool

## Getting Started, Installation, and Setup

### Prerequisites

- Python 3.8 or higher
- Git
- A virtual environment tool (recommended)

### System Requirements

- Operating System: Linux (tested)
- Multi-monitor setup supported
- Access to Cursor AI application

### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cursor-auto-accept
cd cursor-auto-accept
```

2. Run the setup script to initialize the project:
```bash
./setup.sh
```

The setup script will:
- Create necessary project directories
- Set appropriate file permissions
- Create a Python virtual environment
- Install required dependencies

### Dependencies

The project requires the following Python packages (automatically installed):
- opencv-python (>=4.8.0)
- numpy (>=1.24.0)
- pyautogui (>=0.9.54)
- pillow (>=10.0.0)
- mss (>=9.0.1)

### Development Environment Setup

1. Activate the virtual environment:
```bash
source venv/bin/activate
```

2. Verify installation by checking the log file:
```bash
tail temp/logs/clickbot.log
```

### Calibration Process

Before using the bot, you must calibrate it for each monitor:

1. Stop any running bot instances:
```bash
./stop_clickbot.sh
```

2. Run calibration for all monitors:
```bash
source venv/bin/activate
python cursor_auto_accept.py --capture
```

Or for a specific monitor (0-based index):
```bash
python cursor_auto_accept.py --capture --monitor 0
```

### Running the Application

Start the bot:
```bash
./start_clickbot.sh
```

Stop the bot:
```bash
./stop_clickbot.sh
```

## Usage

This tool is a ClickBot designed for automated UI interaction, with configurable settings for scanning and clicking interactions.

### Basic Usage

To run the ClickBot, use the following command:

```bash
python main.py
```

### Command Line Options

The ClickBot supports several command-line options to customize its behavior:

- `--debug`: Enable debug mode for detailed logging and additional diagnostic information
- `--interval FLOAT`: Set the scan interval in seconds (default: 3.0)
- `--confidence FLOAT`: Set the minimum confidence threshold for match detection (default: 0.8)

### Example Commands

1. Run with default settings:
```bash
python main.py
```

2. Run in debug mode with a slower scan interval:
```bash
python main.py --debug --interval 5.0
```

3. Adjust confidence threshold for more precise matching:
```bash
python main.py --confidence 0.9
```

### Options Explained

- `--debug`: When enabled, the bot will:
  - Log more detailed information about matches
  - Save debug images of screen captures and matches
  - Provide verbose logging for troubleshooting

- `--interval`: Controls how frequently the bot scans the screen for matches
  - Lower values increase responsiveness but consume more system resources
  - Higher values reduce CPU usage but may slow down interaction detection

- `--confidence`: Determines the minimum template matching confidence
  - Values range from 0.0 to 1.0
  - Higher values (e.g., 0.9) require more precise matches
  - Lower values (e.g., 0.7) allow more lenient matching

### Stopping the Bot

To stop the ClickBot, use a keyboard interrupt (Ctrl+C). The bot will perform a clean shutdown and log the termination.

## Project Structure

The project is organized into several key directories and files that support its functionality:

### Root Directory
The root directory contains the main application scripts, configuration files, and shell scripts for managing the project:
- `main.py`: Primary entry point for the application
- `clickbot.py`: Core bot implementation
- `cursor_auto_accept.py`: Auto-acceptance functionality
- `run_bot.sh`: Script to run the bot
- `start_clickbot.sh`: Script to start the bot
- `stop_clickbot.sh`: Script to stop the bot
- `requirements.txt`: Python dependencies
- `setup.sh`: Setup script for the project

### Subdirectories

#### `assets/`
Stores image assets and configuration files for different monitor setups:
- `backup/`: Contains backup image and coordinate files
- `monitor_0/`: Monitor-specific assets and click coordinates
- `monitor_2/`: Additional monitor-specific assets

#### `debug/`
Contains debug-related images and diagnostic files:
- Image files for template matching
- Correlation and match visualization images
- Screen and template snapshots

#### `cursor-instructions/`
Documentation and instruction files:
- `features.md`: Feature descriptions
- `github-process.md`: GitHub-related instructions
- `notes.md`: Project notes
- `readme.md`: Additional project documentation

#### `images/`
Stores various project-related images:
- UI element images
- Debug and error icons
- Field and target images

#### `temp/`
Temporary files and logs:
- `clickbot.pid`: Process ID file
- `logs/`: Log file storage

### Test and Analysis Scripts
Several scripts for testing and analysis:
- `test_clickbot.py`: Main test suite
- `test_error_recovery.py`: Error recovery tests
- `test_matcher.py`: Image matching tests
- `analyze_calibration.py`: Calibration analysis
- `analyze_hover_results.py`: Hover result analysis
- `analyze_template.py`: Template analysis script

### Configuration and Utility Scripts
- `logging_config.py`: Logging configuration
- `image_matcher.py`: Image matching utilities
- `error_recovery.py`: Error handling and recovery
- `hover_calibrate.py`: Hover calibration functionality
- `extension.js`: Potential browser/extension integration
- `cursor-plugin.json`: Plugin configuration

This structure supports a modular approach to the bot's functionality, with clear separation of concerns between core logic, assets, debugging, and testing components.

## Additional Notes

### Performance Considerations

The bot is designed with efficiency in mind, with several key performance optimizations:
- Low-frequency screen scanning (0.2 seconds per cycle)
- Configurable confidence thresholds for image matching
- Rate limiting to prevent excessive system load
- Minimal resource consumption during idle periods

### Security and Privacy

The tool operates locally and does not transmit any data externally. Calibration images are stored only on the user's machine in the `assets/` directory. Sensitive interactions are logged minimally in `temp/logs/clickbot.log`.

### Known Limitations

- Requires a consistent, stable user interface for accurate button detection
- Performance may vary across different screen resolutions and monitor configurations
- Relies on visual template matching, which can be sensitive to UI changes

### Compatibility

Primarily tested with:
- Python 3.8+
- Linux and potentially macOS environments
- Cursor AI IDE plugin
- Multiple monitor setups

### Future Development

Potential areas for future enhancement:
- Advanced error handling
- More robust multi-monitor support
- Enhanced calibration wizard
- Improved logging and diagnostics

## Contributing

We welcome contributions to the Cursor Auto Accept project! Here are some guidelines to help you contribute effectively:

### Branch Strategy
- Create a new branch for each major feature or significant change
- Initial branch names can use a timestamp, which can later be renamed to a more descriptive name
- Commit your work to the branch after each group of related changes

### Contribution Process
1. Fork the repository
2. Create a new branch from `main`
3. Make your changes
4. Write or update tests for your changes
5. Ensure all tests pass by running the test suite
6. Submit a pull request with a clear description of your changes

### Code Requirements
- Maintain the existing code style and formatting
- Write clear, concise, and well-documented code
- Include type hints where possible
- Add or update tests to cover new functionality

### Testing
- The project includes multiple test files: `test_clickbot.py`, `test_error_recovery.py`, `test_final.py`, and `test_matcher.py`
- Ensure all existing tests pass before submitting a pull request
- Add new tests for any new functionality or bug fixes

### Dependency Management
- Use `requirements.txt` for managing project dependencies
- If you add a new dependency, update the `requirements.txt` file

### Setup for Development
- Follow the project's standard setup process in the Installation section
- Use the virtual environment created by `setup.sh`
- Test your changes thoroughly across different monitor configurations

### Reporting Issues
- Use GitHub Issues to report bugs or suggest improvements
- Provide detailed information, including steps to reproduce the issue
- Include your operating system, Python version, and any relevant log files when reporting bugs

### Code of Conduct
- Be respectful and constructive in all interactions
- Help maintain a welcoming and inclusive community

## License

This project is licensed under the [MIT License](LICENSE). 

The MIT License is a permissive free software license that allows you to:
- Use the software commercially
- Modify the software
- Distribute the software
- Privately use the software

### Conditions
- Include the original copyright notice
- Include the license text when distributing

### Limitations
- Software is provided "as is" without warranties
- Authors are not liable for damages resulting from use of the software