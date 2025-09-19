#!/usr/bin/env python3
"""
Configuration management for timelapse application.
Handles loading, saving, and accessing configuration settings.
"""

import json
import os
from typing import Dict, Any

DEFAULT_CONFIG = {
    'interval': 5,  # seconds between shots
    'resolution': '1920x1080',  # Video output resolution
    'quality': 85,
    'is_running': False,
    'auto_generate_video': True,  # Automatically generate video at end of session
    'auto_delete_images': True,   # Automatically delete images after video generation
    'video_fps': 30,              # Frames per second for video
    'video_quality': 23,          # Video quality (lower is better for FFmpeg)
    'video_method': 'ffmpeg',     # Video generation method: 'ffmpeg' or 'opencv'
    'scheduled_video_creation': False,  # Enable daily video creation
    'continuous_session_id': None,  # ID for the continuous session
    'daily_video_time': '18:00',  # Daily time to create video (HH:MM format)
    'hflip': False,              # Horizontal flip (mirror image)
    'vflip': False               # Vertical flip (upside down)
}


class Config:
    """Simple configuration manager for timelapse settings."""
    
    def __init__(self, config_file=None):
        if config_file is None:
            # Use system config path if running as service, otherwise local
            if os.path.exists("/var/lib/timelapse"):
                config_file = "/var/lib/timelapse/config/timelapse_config.json"
            else:
                config_file = "timelapse_config.json"
            # Use system config path if running as service, otherwise local
            if os.path.exists("/var/lib/timelapse"):
                config_file = "/var/lib/timelapse/config/timelapse_config.json"
            else:
                config_file = "timelapse_config.json"
            # Use system config path if running as service, otherwise local
            if os.path.exists("/var/lib/timelapse"):
                config_file = "/var/lib/timelapse/config/timelapse_config.json"
            else:
                config_file = "timelapse_config.json"
            # Use system config path if running as service, otherwise local
            if os.path.exists("/var/lib/timelapse"):
                config_file = "/var/lib/timelapse/config/timelapse_config.json"
            else:
                config_file = "timelapse_config.json"
            # Use system config path if running as service, otherwise local
            if os.path.exists("/var/lib/timelapse"):
                config_file = "/var/lib/timelapse/config/timelapse_config.json"
            else:
                config_file = "timelapse_config.json"
        self.config_file = config_file
        self._config = self.load()
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file, return defaults if file doesn't exist."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    config = DEFAULT_CONFIG.copy()
                    config.update(loaded_config)
                    return config
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config file: {e}. Using defaults.")
        
        return DEFAULT_CONFIG.copy()
    
    def save(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except IOError as e:
            print(f"Error saving config file: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value by key."""
        return self._config.get(key, default)
    
    def set(self, key: str, value) -> None:
        """Set configuration value and save to file."""
        self._config[key] = value
        self.save()
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values and save to file."""
        self._config.update(updates)
        self.save()
    
    @property
    def data(self) -> Dict[str, Any]:
        """Get a copy of all configuration data."""
        return self._config.copy()
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._config = self.load()
