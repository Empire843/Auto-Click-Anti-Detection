"""
Auto-Click Tool - Entry Point
Record and Replay mouse trajectories.
"""

import sys
import os

# Ensure imports from current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import AutoClickApp


def main():
    app = AutoClickApp()
    app.mainloop()


if __name__ == "__main__":
    main()
