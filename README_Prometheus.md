# ClickBot: Multi-Monitor UI Automation and Intelligent Screen Interaction Tool

## Project Overview

ClickBot is an advanced automated UI interaction tool designed to intelligently detect, locate, and interact with specific UI elements across multiple monitor configurations. The project provides a sophisticated image recognition and automated clicking solution with robust error handling and monitoring capabilities.

### Key Features

- **Intelligent Screen Scanning**: Automatically detects and scans multiple monitors to locate target application windows
- **Adaptive Image Matching**: Uses advanced computer vision techniques to find UI elements with configurable confidence thresholds
- **Multi-Monitor Support**: Can identify and interact with applications across different monitors
- **Robust Error Recovery**: Implements comprehensive error detection and recovery mechanisms
- **Configurable Operation**: Supports debug mode, customizable scan intervals, and confidence settings
- **Logging and Monitoring**: Detailed logging with file and console output for tracking bot activities

### Purpose

The primary purpose of ClickBot is to automate repetitive UI interactions by:
- Identifying specific screen elements with high precision
- Performing automated clicks on detected targets
- Providing a flexible framework for UI automation tasks
- Handling potential error states and recovery scenarios

ClickBot is particularly useful for scenarios requiring consistent, repeatable UI interactions, such as testing, data entry, or workflow automation.

## Getting Started, Installation, and Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Basic terminal/command line knowledge

### System Requirements

- Operating System: Linux (recommended), macOS, or Windows
- Supported Monitors: Multi-monitor setup supported
- Cursor AI installed and configured

### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cursor-auto-accept.git
cd cursor-auto-accept
```

2. Run the setup script to initialize the project:
```bash
./setup.sh
```

This script will:
- Create necessary directories
- Set up file permissions
- Create a Python virtual environment
- Install required dependencies

### Dependencies

The project requires the following Python packages (automatically installed):
- opencv-python (≥ 4.8.0)
- numpy (≥ 1.24.0)
- pyautogui (≥ 0.9.54)
- pillow (≥ 10.0.0)
- mss (≥ 9.0.1)

### Development Environment Setup

1. Activate the virtual environment:
```bash
source venv/bin/activate
```

2. Verify installation by checking dependencies:
```bash
pip list
```

### Initial Configuration

Before first use, you must calibrate the bot for each monitor:

1. Ensure no bot instances are running:
```bash
./stop_clickbot.sh
```

2. Start calibration mode:
```bash
# Calibrate all monitors
python cursor_auto_accept.py --capture

# Or calibrate a specific monitor (0-based index)
python cursor_auto_accept.py --capture --monitor 0
```

3. Follow on-screen calibration instructions:
- Move Cursor to the target monitor
- Trigger an AI prompt
- Position mouse over the accept button
- Keep mouse still for 5 seconds
- Wait for confirmation

### Starting the Bot

```bash
./start_clickbot.sh
```

### Stopping the Bot

```bash
./stop_clickbot.sh
```

## Usage

The ClickBot is an automated screen interaction tool that finds and clicks on specific targets based on image matching.

### Basic Usage

To run the ClickBot, use the following command:

```bash
python3 clickbot.py
```

This will start the bot, which continuously scans the screen for a predefined target image and automatically clicks on it when found.

### Running with Start Script

For a more robust startup, use the provided shell script:

```bash
./run_bot.sh
```

This script handles platform-specific terminal launching and ensures the bot runs with unbuffered Python output.

### Key Behaviors

- The bot uses a default target image located at `images/target.png`
- It checks the screen at regular intervals (default 1-second checks)
- Clicks are performed only when a high-confidence match is found
- Includes built-in logging to `temp/logs/clickbot.log`

### Configuration Options

While the current version doesn't support command-line flags, you can modify these parameters in the source code:
- Adjust the image matching threshold
- Change the screen check interval
- Customize logging settings

### Important Notes

- Move the mouse to a screen corner to abort the bot (PyAutoGUI failsafe)
- Requires a target image to be present in the `images` directory
- Best used in environments with predictable screen layouts

## Configuration

### Configuration Files

#### Plugin Configuration
The project uses a `cursor-plugin.json` configuration file that defines plugin settings for Cursor AI integration:

```json
{
    "cursorAutoAccept.enabled": true
}
```

Key configuration options:
- `cursorAutoAccept.enabled`: A boolean flag to enable/disable automatic acceptance of AI prompts (default: `true`)

#### Logging Configuration
Logging can be configured programmatically using the `setup_logging()` function in `logging_config.py`. The logging configuration supports:

- Configurable log levels (DEBUG or INFO)
- Rotating file logs with the following characteristics:
  - Maximum log file size: 10MB
  - Backup log files: Up to 5 previous logs
  - Log location: `./logs/` directory
  - Log filename: Uses the component name (e.g., `clickbot.log`)

### Logging Modes
Two primary logging modes are supported:
- Standard mode (default): Logs INFO level messages
- Debug mode: Logs more verbose DEBUG level messages

### Customization
To customize logging, modify the `setup_logging()` function parameters when initializing logging for a specific component.

## Technologies Used

### Programming Languages
- Python (3.x)

### Core Libraries and Frameworks
- OpenCV (opencv-python): Computer vision and image processing
- NumPy: Numerical computing and array operations
- PyAutoGUI: GUI automation and screen interaction
- Pillow (PIL): Image manipulation and processing
- MSS: Cross-platform screen capture

### Development and Testing Tools
- pytest (implied by test files): Unit testing framework
- Logging: Python's built-in logging module

### Additional Tools
- Bash Shell Scripts: For project management (run_bot.sh, start_clickbot.sh, stop_clickbot.sh)
- JSON: Configuration management (cursor-plugin.json)

### Platforms
- Cross-platform (supports multiple operating systems)

### Image Processing Capabilities
- Template matching
- Screen capture
- Image correlation analysis

## Additional Notes

### Performance Considerations

The bot uses template matching and image recognition techniques, which can impact system performance. Key performance factors include:
- Image processing complexity
- Number of monitors being monitored
- System hardware capabilities

### Security and Privacy

- The tool only interacts with UI elements and does not access or modify Cursor's internal workings
- Calibration images are stored locally in the `assets/` directory
- Logging is limited to bot activity and does not capture AI prompt contents

### Limitations

- Requires visual recognition of the accept button, which may fail under:
  - Rapidly changing UI layouts
  - Non-standard display configurations
  - Extremely low contrast or obscured buttons
- Relies on pixel-perfect matching, so minor UI changes can disrupt functionality

### Future Potential Improvements

Possible areas for future development:
- More robust button detection algorithms
- Enhanced multi-monitor support
- Configurable confidence thresholds
- Dynamic UI adaptation mechanisms

### Compatibility

Verified to work with:
- Python 3.8+
- Cursor AI versions as of project creation
- Primary operating systems (Linux, macOS, Windows)

### Community and Support

- Report issues on the GitHub repository
- Contributions welcome via pull requests
- Test coverage provided through included test scripts

### Experimental Features

Some scripts in the repository (like `analyze_calibration.py` and `analyze_hover_results.py`) are experimental and may be used for development and debugging purposes.

## Contributing

We welcome contributions to the Cursor Auto Accept project! To ensure a smooth collaboration, please follow these guidelines:

### Branch Strategy

- Create a new branch for each major feature or significant change
- Use a timestamp-based naming convention for new branches (e.g., `feature/2023-09-15-new-monitor-support`)
- Rename the branch to a more descriptive name once the work is more defined

### Commit Guidelines

- Commit your work after every group of changes related to a specific improvement or feature
- Write clear, concise commit messages that describe the purpose of the changes
- Push your work to the branch after each commit

### Code Contributions

- Ensure your code follows the existing project structure and coding style
- Add or update tests for any new functionality
- Verify that all existing tests pass before submitting a pull request
- Include comments and documentation for new features or significant changes

### Testing

- Run the existing test suite before submitting a pull request:
  ```bash
  python -m pytest test_clickbot.py test_error_recovery.py test_matcher.py test_final.py
  ```
- If adding new functionality, create corresponding test cases
- Ensure test coverage is maintained or improved

### Reporting Issues

- Use GitHub Issues to report bugs, request features, or discuss improvements
- Provide detailed information, including:
  - Steps to reproduce (for bugs)
  - Expected behavior
  - Actual behavior
  - Environment details (OS, Python version, etc.)

### Pull Request Process

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to your branch
5. Open a pull request with a clear description of your changes

### Environment Setup

- Use the provided `setup.sh` script to set up the development environment
- Ensure you're using Python 3.8 or newer
- Install all requirements from `requirements.txt`

By contributing to this project, you agree to abide by these guidelines and the project's code of conduct.

## License

This project is licensed under the MIT License. For the full license text, please see the [LICENSE](LICENSE) file in the repository.

### Key Permissions
- Commercial use
- Modification
- Distribution
- Private use

### Conditions
- License and copyright notice must be included
- The software is provided "as is" without warranties

For complete details, refer to the full MIT License text.