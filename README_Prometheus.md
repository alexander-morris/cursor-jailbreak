# Cursor Auto Accept: AI-Powered Multi-Monitor UI Interaction Bot

## Project Overview

Automated UI interaction tool designed to intelligently detect and interact with specific screen elements using advanced image matching and computer vision techniques. The project provides a robust, configurable bot that can autonomously scan multiple monitors, locate target UI elements, and perform precision clicks with high confidence and error recovery mechanisms.

### Key Features

- **Multi-Monitor Support**: Dynamically detects and scans multiple monitors to locate application windows
- **Intelligent Image Matching**: Uses advanced computer vision techniques to identify UI elements with configurable confidence thresholds
- **Adaptive Error Handling**: Includes sophisticated error recovery mechanisms to maintain bot stability
- **Flexible Configuration**: Supports runtime configuration of scan intervals, confidence levels, and debug modes
- **Comprehensive Logging**: Provides detailed logging for tracking bot activities and troubleshooting

### Core Capabilities

- Automated screen scanning and element detection
- Precision mouse clicking on identified targets
- Automatic error state detection and recovery
- Customizable performance parameters
- Cross-platform compatibility (works on systems with multiple monitors)

### Primary Use Cases

The bot is particularly useful for:
- Automating repetitive UI interactions
- Testing user interface workflows
- Performing consistent, precise screen navigation
- Monitoring and interacting with specific application states

The system is designed to be both powerful and adaptable, providing developers and testers with a flexible tool for screen-based automation tasks.

## Getting Started, Installation, and Setup

### Prerequisites

- Python 3.8 or higher
- Git
- A terminal/command line interface

### System Requirements

- Operating System: Linux, macOS, or Windows
- Recommended: Multi-monitor setup for full functionality

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
- Install required dependencies

### Dependencies

The project requires the following Python packages (automatically installed by setup):
- OpenCV (>= 4.8.0)
- NumPy (>= 1.24.0)
- PyAutoGUI (>= 0.9.54)
- Pillow (>= 10.0.0)
- MSS (>= 9.0.1)

### Activation and Configuration

#### Calibration (Required)

Before using the bot, you must calibrate it for each monitor:

1. Activate the virtual environment:
```bash
source venv/bin/activate
```

2. Run calibration:
```bash
# Calibrate all monitors
python cursor_auto_accept.py --capture

# Or calibrate a specific monitor (0-based index)
python cursor_auto_accept.py --capture --monitor 0
```

3. Follow on-screen instructions:
- Move Cursor to the target monitor
- Trigger an AI prompt
- Move mouse over the accept button
- Keep mouse still for 5 seconds
- Wait for confirmation

### Running the Bot

Start the bot:
```bash
./start_clickbot.sh
```

Stop the bot:
```bash
./stop_clickbot.sh
```

### Monitoring

Check bot activity in the log file:
```bash
tail -f temp/logs/clickbot.log
```

## Additional Notes

### Performance Considerations

The Cursor Auto Accept bot is designed with careful performance optimization in mind:
- Limited to 8 clicks per minute to prevent overwhelming the system
- Uses a configurable confidence threshold of 0.8 (80% match) for button detection
- Lightweight monitoring with a 0.2-second search interval
- Minimal system resource consumption

### Security and Privacy

The tool operates locally and does not transmit any data externally. All calibration images and logs are stored on the user's local machine, ensuring complete privacy.

### Compatibility

#### Supported Environments
- Operating Systems: Linux (primary support)
- Python Versions: 3.8+
- Multi-monitor setups with independent calibration

#### Known Limitations
- Requires manual calibration for each monitor
- Dependent on consistent UI elements in Cursor AI
- Performance may vary based on screen resolution and monitor configuration

### Future Roadmap

Planned enhancements include:
- More robust multi-monitor support
- Advanced error handling and recovery mechanisms
- Extended visualization and debugging tools
- Machine learning-based button detection improvements

### Debugging and Diagnostics

The bot provides comprehensive logging and diagnostic capabilities:
- Detailed activity log at `temp/logs/clickbot.log`
- Debug image generation in the `debug/` directory
- Configurable logging levels for in-depth troubleshooting

### Community and Support

- Report issues on the GitHub repository
- Contributions welcome via pull requests
- Join our discussion forums for community support and feature requests

## Contributing

We welcome contributions to this project! To help maintain code quality and consistency, please follow these guidelines:

### Branch Management
- Create a new branch for each major feature or significant change
- Use a descriptive branch name that reflects the feature or improvement
- Initially, you can use a timestamp for the branch name and rename it later if desired

### Commit Guidelines
- Commit your work after completing a specific improvement or feature
- Write clear, concise commit messages that describe the changes
- Push your work to the branch after each commit

### Testing
- All code changes must include appropriate unit tests
- Use the existing test framework in `test_clickbot.py` as a reference
- Ensure all tests pass before submitting a pull request
- Write tests that cover different scenarios, including edge cases

### Code Quality
- Follow Python best practices and maintain clean, readable code
- Use type hints and docstrings for functions and classes
- Ensure your code does not introduce new warnings or linting errors

### Documentation
- Update relevant documentation when adding new features
- Document any significant changes in the README or other documentation files
- Add comments to explain complex logic or non-obvious implementations

### Pull Request Process
- Ensure your code is well-tested and passes all existing tests
- Include a clear description of the changes in your pull request
- Be prepared to address review comments and make necessary modifications

### Security
- Report any potential security vulnerabilities responsibly
- Do not implement major features without explicit discussion
- Prioritize security and efficiency in your contributions

We appreciate your help in improving this project!

## License

This project is licensed under the MIT License. 

### Key License Terms

- Free to use, modify, and distribute
- Attribution appreciated but not required
- Software provided "as is" without warranty
- Commercial use permitted
- Modifications and derivative works allowed

For the complete license text, please refer to the [MIT License](https://opensource.org/licenses/MIT).