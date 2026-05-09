"""
Utility functions cho Auto-Click Tool.
"""

import os
import sys
import json
import time


def get_app_dir() -> str:
    """Lấy thư mục chứa app (hỗ trợ cả dev và exe)."""
    if getattr(sys, 'frozen', False):
        # Đang chạy từ exe (PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # Đang chạy từ source
        return os.path.dirname(os.path.abspath(__file__))


CONFIG_FILE = os.path.join(get_app_dir(), "autoclick_config.json")
RECORDINGS_DIR = os.path.join(get_app_dir(), "recordings")


def load_config() -> dict:
    """Tải config từ file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(config: dict):
    """Lưu config ra file."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Lỗi lưu config: {e}")


def get_recordings_dir() -> str:
    """Lấy thư mục recordings (từ config hoặc mặc định)."""
    config = load_config()
    return config.get("recordings_dir", RECORDINGS_DIR)


def set_recordings_dir(path: str):
    """Cập nhật thư mục recordings trong config."""
    global RECORDINGS_DIR
    config = load_config()
    config["recordings_dir"] = path
    save_config(config)
    RECORDINGS_DIR = path


def ensure_recordings_dir():
    """Tạo thư mục recordings nếu chưa tồn tại."""
    rec_dir = get_recordings_dir()
    os.makedirs(rec_dir, exist_ok=True)


def format_duration(seconds: float) -> str:
    """Format thời lượng thành chuỗi mm:ss.ms"""
    if seconds < 0:
        seconds = 0
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 100)
    if mins > 0:
        return f"{mins:02d}:{secs:02d}.{ms:02d}"
    return f"{secs:02d}.{ms:02d}s"


def format_number(n: int) -> str:
    """Format số với dấu phân cách hàng nghìn."""
    return f"{n:,}"


def get_timestamp() -> str:
    """Lấy timestamp hiện tại cho tên file."""
    return time.strftime("%Y%m%d_%H%M%S")


def clamp(value, min_val, max_val):
    """Giới hạn giá trị trong khoảng [min_val, max_val]."""
    return max(min_val, min(value, max_val))
