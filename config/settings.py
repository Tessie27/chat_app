"""
Configuration management for Secure Chat
"""

import os
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.portable import get_config_dir, load_config, save_config


class Settings:
    """Application settings manager"""

    DEFAULT_SETTINGS = {
        "theme": "dark",
        "font_size": 11,
        "save_history": True,
        "max_history": 100,
        "auto_reconnect": False,
        "notifications": True,
        "sound_alerts": False,
        "encryption": {"enabled": True, "algorithm": "AES-256", "key_rotation_days": 7},
        "connection": {"timeout": 8, "buffer_size": 4096, "keepalive": True},
        "privacy": {"show_typing": False, "read_receipts": False, "last_seen": True},
    }

    def __init__(self):
        self.config_file = get_config_dir() / "settings.json"
        self.settings = self.load()

    def load(self):
        """Load settings from file"""
        settings = load_config("settings.json")
        if not settings:
            return self.DEFAULT_SETTINGS.copy()

        # Merge with defaults (ensure all keys exist)
        merged = self.DEFAULT_SETTINGS.copy()
        merged.update(settings)
        return merged

    def save(self):
        """Save settings to file"""
        return save_config("settings.json", self.settings)

    def get(self, key, default=None):
        """Get a setting value"""
        keys = key.split(".")
        value = self.settings
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key, value):
        """Set a setting value"""
        keys = key.split(".")
        target = self.settings
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        self.save()

    def reset(self):
        """Reset to default settings"""
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.save()


class ServerConfig:
    """Server configuration"""

    DEFAULT_CONFIG = {
        "host": "0.0.0.0",
        "port": 5555,
        "password": None,
        "max_clients": 100,
        "rate_limit": {"messages_per_second": 5, "burst": 10},
        "rooms": {"max_rooms": 50, "default_room": "General"},
        "logging": {
            "level": "INFO",
            "file": "server.log",
            "max_size_mb": 10,
            "backup_count": 3,
        },
        "security": {
            "require_auth": False,
            "max_login_attempts": 3,
            "ban_duration_minutes": 60,
            "allowed_ips": [],
        },
    }

    def __init__(self, config_file=None):
        if config_file:
            self.config_file = Path(config_file)
        else:
            self.config_file = get_config_dir() / "server_config.json"
        self.config = self.load()

    def load(self):
        """Load server config"""
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                return json.load(f)
        return self.DEFAULT_CONFIG.copy()

    def save(self):
        """Save server config"""
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)


class UserProfile:
    """User profile management"""

    def __init__(self, username):
        self.username = username
        self.profile_file = get_config_dir() / f"user_{username}.json"
        self.profile = self.load()

    def load(self):
        """Load user profile"""
        if self.profile_file.exists():
            with open(self.profile_file, "r") as f:
                return json.load(f)
        return {
            "username": self.username,
            "display_name": self.username,
            "status": "online",
            "avatar": None,
            "public_key": None,
            "friends": [],
            "blocked": [],
            "preferences": {"theme": "dark", "notifications": True},
            "stats": {"messages_sent": 0, "rooms_joined": 0, "connections": 0},
        }

    def save(self):
        """Save user profile"""
        with open(self.profile_file, "w") as f:
            json.dump(self.profile, f, indent=2)

    def increment_stat(self, stat_name):
        """Increment a statistic"""
        if stat_name in self.profile["stats"]:
            self.profile["stats"][stat_name] += 1
            self.save()
