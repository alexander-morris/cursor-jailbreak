"""
Configuration settings for the Cursor Auto Accept application.
"""

from pathlib import Path

class ClickBotConfig:
    """Configuration settings for the application."""
    
    # Directories
    BASE_DIR = Path(__file__).parent.parent.parent
    ASSETS_DIR = BASE_DIR / "assets"
    DEBUG_DIR = BASE_DIR / "debug"
    
    # Matching parameters
    MATCH_THRESHOLD = 0.8
    SEARCH_MARGIN_X = 10
    SEARCH_MARGIN_Y = 80
    
    # UI settings
    WINDOW_TITLE = "Cursor Auto Accept"
    WINDOW_SIZE = "800x600" 