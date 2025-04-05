# Cursor Auto Accept CLI

## Project Overview

Cursor Auto Accept is an intelligent CLI tool designed to automatically accept AI suggestions in the Cursor AI development environment. This automation tool helps developers streamline their workflow by reducing manual intervention during code generation and suggestion acceptance.

Key features include:
- Multi-monitor support with per-monitor button detection
- Intelligent button recognition using template matching
- Configurable click rate limiting
- Automatic error recovery and logging
- Precise cursor position management

### Use Cases
- Accelerate AI-assisted coding workflows
- Reduce repetitive button clicking during pair programming
- Enable hands-free code suggestion review
- Support developers working across multiple monitors

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Installation Methods

#### Method 1: Direct Installation
```bash
git clone https://github.com/yourusername/cursor-auto-accept.git
cd cursor-auto-accept
./setup.sh
source venv/bin/activate
```

#### Method 2: Virtual Environment
```bash
python3 -m venv cursor-auto-accept
source cursor-auto-accept/bin/activate
pip install opencv-python numpy pyautogui pillow mss
```

### Dependencies
The tool requires the following Python libraries:
- OpenCV (`opencv-python`) ≥ 4.8.0
- NumPy ≥ 1.24.0
- PyAutoGUI ≥ 0.9.54
- Pillow ≥ 10.0.0
- MSS ≥ 9.0.1

## Usage

### Basic Command Structure
```bash
python cursor_auto_accept.py [OPTIONS]
```

### Common Commands

1. **Start Auto Accept Bot**
   ```bash
   ./start_clickbot.sh
   ```
   Starts the bot, monitoring all connected monitors for Cursor AI suggestion buttons.

2. **Stop Auto Accept Bot**
   ```bash
   ./stop_clickbot.sh
   ```
   Halts the bot and releases system resources.

3. **Calibrate Monitors**
   ```bash
   # Calibrate all monitors
   python cursor_auto_accept.py --capture

   # Calibrate specific monitor
   python cursor_auto_accept.py --capture --monitor 0
   ```

### Configuration Options

| Option | Description | Default Value |
|--------|-------------|---------------|
| `--capture` | Enter calibration mode | False |
| `--monitor` | Specify monitor index | All monitors |
| `--confidence` | Set template matching threshold | 0.8 |
| `--rate-limit` | Maximum clicks per minute | 8 |

## Advanced Configuration

### Environment Variables
- `CURSOR_AUTO_ACCEPT_RATE`: Override default click rate
- `CURSOR_AUTO_ACCEPT_LOGGING`: Enable/disable detailed logging

### Logging
Logs are stored in `temp/logs/clickbot.log`. Monitor real-time logs with:
```bash
tail -f temp/logs/clickbot.log
```

## Troubleshooting

### Common Issues
- **No Clicks Detected**: 
  - Recalibrate monitor
  - Check Cursor AI suggestion button visibility
  - Verify Python environment

- **Multiple Bot Instances**: 
  - Check `temp/clickbot.pid`
  - Use `stop_clickbot.sh` to terminate existing instances

## Project Structure
```
cursor-auto-accept/
├── assets/               # Monitor-specific calibration images
├── temp/                 # Runtime files and logs
├── cursor_auto_accept.py # Main CLI script
├── setup.sh              # Installation script
├── start_clickbot.sh     # Bot start script
└── stop_clickbot.sh      # Bot stop script
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-detection-method`)
3. Commit changes (`git commit -m 'Add multi-resolution support'`)
4. Push to branch (`git push origin feature/new-detection-method`)
5. Create Pull Request

### Development Setup
```bash
python -m venv dev-env
source dev-env/bin/activate
pip install -r requirements.txt
pip install pytest
pytest test_clickbot.py
```

## License

MIT License - See LICENSE file for complete details.

## Support

If you encounter issues or have suggestions, please file an issue on the GitHub repository or contact the maintainers.