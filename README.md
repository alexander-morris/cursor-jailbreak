# Cursor Auto Accept

A tool for automatically accepting Cursor's AI suggestions using robust multi-scale template matching.

## Features

- Multi-monitor support with per-monitor calibration
- Gold standard button detection algorithm:
  - Multi-scale template matching (0.995x - 1.005x)
  - Edge detection pre-filtering
  - Weighted scoring system (direct match, edge overlap, edge confidence)
- Rate limiting and cursor position restoration
- Detailed logging and error handling

## Setup

1. Clone this repository:
```bash
git clone https://github.com/yourusername/cursor-auto-accept
cd cursor-auto-accept
```

2. Create and activate a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Initial Calibration

Before first use, you need to calibrate the bot:

1. Run the main application:
```bash
python main.py
```

2. The application will:
   - Detect all available monitors
   - Guide you through calibrating each button
   - Save calibration data for future use

3. During calibration:
   - Move your mouse over each button when prompted
   - Keep it still for the countdown
   - The app will capture both pre-click and post-click states
   - Repeat for all required buttons

### Running the Bot

After calibration:

1. Start the application:
```bash
python main.py
```

2. The bot will:
   - Load saved calibration data
   - Begin monitoring for buttons using the gold standard detection algorithm
   - Automatically click detected buttons

### Button Detection Algorithm

The bot uses a sophisticated button detection approach:

1. **Pre-filtering**:
   - Edge detection with optimized Canny parameters (30, 120)
   - Edge dilation for better connectivity

2. **Multi-scale Search**:
   - Scales: 0.995, 1.0, 1.005
   - Search margins: ±100px vertical, ±50px horizontal

3. **Match Quality Scoring**:
   - Direct template matching (65%)
   - Edge overlap ratio (20%)
   - Edge confidence (15%)

## Directory Structure

```
.
├── assets/                     # Calibration data
│   └── monitor_*/             # Per-monitor data
│       ├── button_*_pre.png   # Button templates
│       ├── button_*_post.png  # Post-click states
│       ├── click_coords_*.txt # Click coordinates
│       └── monitor_*.txt      # Monitor info
├── src/                       # Source code
│   ├── core/                  # Core functionality
│   │   ├── button_detector.py # Button detection
│   │   └── calibrator.py      # Calibration
│   └── ui/                    # User interface
├── debug/                     # Debug output
└── main.py                    # Entry point
```

## Requirements

- Python 3.8+
- OpenCV-Python
- MSS (Multi-Screen Shot)
- NumPy
- PyQt5 (for UI)

## Troubleshooting

1. **Button Detection Issues**:
   - Ensure proper lighting conditions
   - Recalibrate if button appearance changes
   - Check debug logs for match quality scores

2. **Monitor Detection**:
   - Verify monitor configuration in system settings
   - Check monitor boundaries in debug output
   - Ensure calibration points are within screen bounds

3. **Performance Issues**:
   - Monitor CPU usage in debug logs
   - Adjust search interval if needed
   - Check for conflicting screen capture tools

## License

MIT License 