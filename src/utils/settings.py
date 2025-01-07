"""
Settings management for the Cursor Auto Accept application.
"""

import json
from pathlib import Path
from src.utils.config import ClickBotConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)

class Settings:
    def __init__(self):
        """Initialize settings."""
        self.settings_file = ClickBotConfig.BASE_DIR / "settings.json"
        self.settings = self._load_settings()
        
    def _load_settings(self):
        """Load settings from file."""
        if not self.settings_file.exists():
            return {}
            
        try:
            with open(self.settings_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return {}
            
    def _save_settings(self):
        """Save settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            
    def get_last_monitor(self):
        """Get last used monitor index."""
        return self.settings.get("last_monitor_index")
        
    def save_last_monitor(self, monitor_index):
        """Save last used monitor index."""
        self.settings["last_monitor_index"] = monitor_index
        self._save_settings()
        logger.info(f"Saved last monitor index: {monitor_index}")
        
    def get(self, key, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)
        
    def set(self, key, value):
        """Set a setting value."""
        self.settings[key] = value
        self._save_settings()
        logger.info(f"Saved setting {key}: {value}")
        
    def save(self):
        """Save all settings."""
        self._save_settings() 