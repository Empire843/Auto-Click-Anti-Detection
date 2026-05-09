"""
Utility functions for Auto-Click Tool.
"""

import os
import sys
import json
import time


def get_app_dir() -> str:
    """Get the directory containing the app (supports both dev and exe)."""
    if getattr(sys, 'frozen', False):
        # Running from exe (PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # Running from source
        return os.path.dirname(os.path.abspath(__file__))


CONFIG_FILE = os.path.join(get_app_dir(), "autoclick_config.json")
RECORDINGS_DIR = os.path.join(get_app_dir(), "recordings")


def load_config() -> dict:
    """Load config from file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(config: dict):
    """Save config to file."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")


def get_recordings_dir() -> str:
    """Get recordings directory (from config or default)."""
    config = load_config()
    return config.get("recordings_dir", RECORDINGS_DIR)


def set_recordings_dir(path: str):
    """Update recordings directory in config."""
    global RECORDINGS_DIR
    config = load_config()
    config["recordings_dir"] = path
    save_config(config)
    RECORDINGS_DIR = path


def ensure_recordings_dir():
    """Create recordings directory if it doesn't exist."""
    rec_dir = get_recordings_dir()
    os.makedirs(rec_dir, exist_ok=True)


def format_duration(seconds: float) -> str:
    """Format duration as mm:ss.ms string."""
    if seconds < 0:
        seconds = 0
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 100)
    if mins > 0:
        return f"{mins:02d}:{secs:02d}.{ms:02d}"
    return f"{secs:02d}.{ms:02d}s"


def format_number(n: int) -> str:
    """Format number with thousands separator."""
    return f"{n:,}"


def get_timestamp() -> str:
    """Get current timestamp for file naming."""
    return time.strftime("%Y%m%d_%H%M%S")


def clamp(value, min_val, max_val):
    """Clamp value to [min_val, max_val] range."""
    return max(min_val, min(value, max_val))
