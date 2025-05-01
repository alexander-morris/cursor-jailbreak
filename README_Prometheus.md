# ClickBot: Automated UI Interaction Tool for Cursor AI Workflows

## Getting Started, Installation, and Setup

### Prerequisites

- Python 3.8+
- pip package manager
- Git (for cloning the repository)

### Dependencies

The project requires the following Python libraries:
- OpenCV (`opencv-python`) >= 4.8.0
- NumPy >= 1.24.0
- PyAutoGUI >= 0.9.54
- Pillow >= 10.0.0
- MSS >= 9.0.1

### Installation Steps

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize project directories and permissions:
   ```bash
   bash setup.sh
   ```

### Development Setup

The project includes shell scripts for convenient management:

- `start_clickbot.sh`: Starts the bot
- `stop_clickbot.sh`: Stops the running bot
- `run_bot.sh`: Runs the bot directly

### Running the Application

For development:
```bash
python main.py
```

For production or background execution, use the provided shell scripts.

### Troubleshooting

- Ensure all dependencies are correctly installed
- Check that you have the necessary system permissions
- Verify Python and pip are correctly configured

## Usage

The ClickBot is a Python-based automated UI interaction tool designed to interact with specific application interfaces by finding and clicking on predefined image targets.

### Basic Usage

Run the bot from the command line using the following syntax:

```bash
python main.py [OPTIONS]
```

### Command Line Options

- `--debug`: Enable debug mode for detailed logging and additional diagnostic information
- `--interval FLOAT`: Set the scan interval in seconds (default: 3.0)
- `--confidence FLOAT`: Set the minimum confidence threshold for image matching (default: 0.8)

### Example Commands

1. Run the bot with default settings:
```bash
python main.py
```

2. Run the bot in debug mode with a custom scan interval:
```bash
python main.py --debug --interval 5.0
```

3. Adjust the confidence threshold for more precise or lenient matching:
```bash
python main.py --confidence 0.9
```

### Debugging and Monitoring

When run with the `--debug` flag, the bot will:
- Provide more detailed logging
- Save debug images of screen captures and matches
- Log additional information about image matching and error recovery

### Matching and Interaction

The bot performs the following key actions:
- Scans the screen for predefined image targets
- Identifies and clicks on targets that meet the confidence threshold
- Implements a cooldown between clicks to prevent rapid interactions
- Handles potential error states with an integrated recovery mechanism

### Stopping the Bot

You can stop the bot using:
- Keyboard interrupt (Ctrl+C)
- Termination signals (SIGINT, SIGTERM)

The bot will gracefully shut down and log the termination event.

## Configuration

Configuration options for this project are implemented through different mechanisms:

### Plugin Configuration

The project includes a Cursor plugin configuration file (`cursor-plugin.json`) with the following settings:

```json
{
    "cursorAutoAccept.enabled": {
        "type": "boolean",
        "default": true,
        "description": "Enable/disable automatic acceptance of prompts"
    }
}
```

This configuration allows toggling the automatic acceptance feature for Cursor AI prompts.

### Logging Configuration

Logging can be configured programmatically using the `setup_logging()` function in `logging_config.py`. Key configuration options include:

- `component_name`: Specifies the name of the logging component
- `debug_mode`: A boolean flag to enable more verbose logging
  - When `True`: Sets logging level to DEBUG
  - When `False`: Sets logging level to INFO

Logging features:
- Automatically creates a `logs` directory
- Generates log files with rotating file handler (maximum 10MB per file, up to 5 backup files)
- Provides both file and console logging
- Log files are named after the component (e.g., `componentname.log`)

### Configuration Locations

Configuration files should be placed in the project's root directory:
- Cursor plugin configuration: `cursor-plugin.json`
- Logging configuration: Managed programmatically via `setup_logging()` function

Note: Custom configuration files beyond these are not present in the current project structure.

## Additional Notes

### Performance Considerations

The auto-accept bot is designed with several performance optimization strategies:
- Rate limited to 8 clicks per minute to prevent system overload
- Low-overhead template matching with a 0.8 confidence threshold
- Minimal CPU usage with 0.2-second search intervals
- Efficient multi-monitor support with per-monitor calibration

### Security and Privacy

#### Click Automation
- Designed to automate repetitive UI interactions with Cursor AI
- Restores cursor position after clicks to minimize UI disruption
- Logs all activities for transparency and debugging

#### System Protection
- Prevents multiple bot instances from running simultaneously
- Uses PID file management to track and control bot processes
- Includes error recovery mechanisms to handle unexpected scenarios

### Compatibility Notes

#### System Requirements
- Tested on Python 3.8+
- Works best with multiple monitor setups
- Requires screen capture capabilities
- Compatible with most modern desktop environments

#### Known Limitations
- Requires manual calibration for each monitor
- Performance may vary based on screen resolution and UI scaling
- Assumes consistent Cursor AI UI across different environments

### Extensibility

#### Customization Points
- Easily configurable through command-line parameters
- Modular design allows for future feature extensions
- Logging system supports detailed troubleshooting

### Future Development

Potential areas for future enhancement:
- Support for more AI development tools
- Enhanced multi-monitor calibration
- Advanced error handling and recovery
- More granular configuration options

## Contributing

We welcome contributions to the Cursor Auto Accept project! By contributing, you help improve the tool for the entire community.

### Contribution Guidelines

#### Branching Strategy
- Create a new branch for each feature or significant change
- Use a clear, descriptive branch name
- Branches should be named with a timestamp initially and can be renamed later for clarity

#### Commit Best Practices
- Commit your work after completing a logical group of changes
- Write clear, concise commit messages that describe the purpose of your changes
- Push your work to the branch after each commit

#### Code Contribution Process
1. Fork the repository
2. Create a new branch from the main branch
3. Make your changes
4. Ensure all existing tests pass
5. Add new tests if applicable
6. Submit a pull request with a clear description of your changes

### Development Setup
- Use Python 3.8 or higher
- Install development dependencies using `requirements.txt`
- Run tests using `pytest` before submitting a pull request

### Reporting Issues
- Use GitHub Issues to report bugs or suggest features
- Provide detailed information about your environment
- Include steps to reproduce the issue
- If possible, include screenshots or log excerpts

### Code Style
- Follow standard Python coding conventions
- Use meaningful variable and function names
- Add docstrings and comments to explain complex logic
- Maintain consistent formatting

### Testing
- All code changes must include appropriate test coverage
- Run the existing test suite before submitting a pull request
- Ensure no new warnings or errors are introduced

### Attribution
By contributing, you agree to license your changes under the project's MIT License.

## License

This project is licensed under the [MIT License](LICENSE). 

#### Key Permissions
- Commercial use
- Modification
- Distribution
- Private use

#### Key Conditions
- License and copyright notice must be included
- The software is provided "as is" without warranties

For the full license details, please see the [LICENSE](LICENSE) file in the repository.