"""
Portable mode utilities - handles configuration storage
"""
import os
import json
import sys
import time
from pathlib import Path

def is_portable():
    """Check if running in portable mode"""
    return os.environ.get("CHAT_PORTABLE", "0") == "1"

def get_config_dir():
    """Get appropriate config directory based on mode"""
    if is_portable():
        # Use local folder for portable mode
        config_dir = Path(os.environ.get("CHAT_CONFIG", "./chat_data"))
    else:
        # Use system config directory
        if sys.platform == "win32":
            config_dir = Path(os.environ.get("APPDATA", "")) / "SecureChat"
        elif sys.platform == "darwin":
            config_dir = Path.home() / "Library" / "Application Support" / "SecureChat"
        else:
            config_dir = Path.home() / ".config" / "securechat"
    
    # Create directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def get_config_path(filename):
    """Get full path for a config file"""
    return get_config_dir() / filename

def save_config(filename, data):
    """Save configuration data"""
    try:
        path = get_config_path(filename)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def load_config(filename, default=None):
    """Load configuration data"""
    try:
        path = get_config_path(filename)
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
    
    return default or {}

def save_history(room, messages):
    """Save chat history for a room"""
    try:
        history_file = get_config_path(f"history_{room}.json")
        # Keep only last 100 messages
        if len(messages) > 100:
            messages = messages[-100:]
        
        with open(history_file, 'w') as f:
            json.dump(messages, f)
        return True
    except Exception:
        return False

def load_history(room):
    """Load chat history for a room"""
    try:
        history_file = get_config_path(f"history_{room}.json")
        if history_file.exists():
            with open(history_file, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return []

def cleanup_old_files(max_age_days=30):
    """Clean up old log/history files"""
    config_dir = get_config_dir()
    now = time.time()
    
    for file in config_dir.glob("*.json"):
        if file.stat().st_mtime < now - (max_age_days * 86400):
            try:
                file.unlink()
            except Exception:
                pass

def get_app_path():
    """Get the path to the application (useful for portable mode)"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return Path(sys.executable).parent
    else:
        # Running as script
        return Path(__file__).parent.parent

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = get_app_path()
    return base_path / relative_path