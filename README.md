# HustleBot Clicker

An automated tool for detecting and interacting with note icons across multiple monitors.

## Features

- Multi-monitor support
- Automatic note icon detection
- Smart prompt interaction with visual verification
- Configurable cooldown between actions
- Robust error handling and logging

## Requirements

- Python 3.x
- OpenCV
- numpy
- pyautogui
- mss

## Installation

1. Clone the repository:
```bash
git clone [your-repo-url]
cd hustlebot_clicker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Place note icon images in the `images` directory:
- `note-with-icon.png`
- `note-text.png`

## Usage

Run the bot:
```bash
python cursor_auto_accept.py
```

The bot will:
1. Detect note icons across all monitors
2. Click the prompt field
3. Type "continue"
4. Submit using Command+Enter (Mac)

## Configuration

- Adjust cooldown time in `NoteDetector.__init__`
- Modify confidence threshold in `find_note`
- Configure prompt position in `type_in_prompt`

## Logging

Logs are written to:
- Console output
- `cursor_bot.log` file

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 