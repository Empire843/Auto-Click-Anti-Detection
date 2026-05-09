"""
Auto-Click Tool - Entry Point
Ghi lại và Phát lại quỹ đạo chuột.
"""

import sys
import os

# Đảm bảo import từ thư mục hiện tại
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import AutoClickApp


def main():
    app = AutoClickApp()
    app.mainloop()


if __name__ == "__main__":
    main()
