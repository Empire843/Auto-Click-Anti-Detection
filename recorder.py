"""
Mouse Recorder Module.
Records all mouse events (movement, clicks, scrolling) using pynput.
"""

import time
import threading
from typing import Callable, Optional

from pynput import mouse
from pynput.mouse import Button

from models import MouseEvent, Recording, EventType, ButtonType


class MouseRecorder:
    """Records mouse events in real-time."""

    # Minimum interval between 2 move events (seconds) to avoid excessive data
    MIN_MOVE_INTERVAL = 0.008  # ~125 samples/sec

    def __init__(self):
        self._recording: Optional[Recording] = None
        self._listener: Optional[mouse.Listener] = None
        self._start_time: float = 0.0
        self._last_move_time: float = 0.0
        self._is_recording: bool = False
        self._lock = threading.Lock()

        # Callbacks for GUI
        self.on_event_recorded: Optional[Callable[[MouseEvent], None]] = None
        self.on_recording_stopped: Optional[Callable[[Recording], None]] = None

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @property
    def current_recording(self) -> Optional[Recording]:
        return self._recording

    @property
    def elapsed_time(self) -> float:
        """Elapsed recording time (seconds)."""
        if self._is_recording and self._start_time > 0:
            return time.time() - self._start_time
        elif self._recording:
            return self._recording.duration
        return 0.0

    def start(self):
        """Start recording mouse events."""
        if self._is_recording:
            return

        import pyautogui
        screen_w, screen_h = pyautogui.size()

        self._recording = Recording(
            screen_width=screen_w,
            screen_height=screen_h
        )
        self._start_time = time.time()
        self._last_move_time = 0.0
        self._is_recording = True

        self._listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll
        )
        self._listener.start()

    def stop(self) -> Optional[Recording]:
        """Stop recording and return the Recording."""
        if not self._is_recording:
            return self._recording

        self._is_recording = False

        if self._listener:
            self._listener.stop()
            self._listener = None

        recording = self._recording

        if self.on_recording_stopped and recording:
            self.on_recording_stopped(recording)

        return recording

    def _get_relative_time(self) -> float:
        """Get relative time since recording started."""
        return time.time() - self._start_time

    def _button_to_str(self, button) -> str:
        """Convert pynput Button to string."""
        if button == Button.left:
            return ButtonType.LEFT
        elif button == Button.right:
            return ButtonType.RIGHT
        elif button == Button.middle:
            return ButtonType.MIDDLE
        return ButtonType.NONE

    def _add_event(self, event: MouseEvent):
        """Add event to recording (thread-safe)."""
        with self._lock:
            if self._recording and self._is_recording:
                self._recording.add_event(event)
                if self.on_event_recorded:
                    self.on_event_recorded(event)

    def _on_move(self, x: int, y: int):
        """Callback when mouse moves."""
        if not self._is_recording:
            return

        current_time = self._get_relative_time()

        # Sampling: skip if too close to previous event
        if current_time - self._last_move_time < self.MIN_MOVE_INTERVAL:
            return

        self._last_move_time = current_time

        event = MouseEvent(
            timestamp=round(current_time, 4),
            event_type=EventType.MOVE,
            x=int(x),
            y=int(y)
        )
        self._add_event(event)

    def _on_click(self, x: int, y: int, button, pressed: bool):
        """Callback when mouse is clicked."""
        if not self._is_recording:
            return

        event = MouseEvent(
            timestamp=round(self._get_relative_time(), 4),
            event_type=EventType.CLICK,
            x=int(x),
            y=int(y),
            button=self._button_to_str(button),
            pressed=pressed
        )
        self._add_event(event)

    def _on_scroll(self, x: int, y: int, dx: int, dy: int):
        """Callback when mouse is scrolled."""
        if not self._is_recording:
            return

        event = MouseEvent(
            timestamp=round(self._get_relative_time(), 4),
            event_type=EventType.SCROLL,
            x=int(x),
            y=int(y),
            scroll_dx=dx,
            scroll_dy=dy
        )
        self._add_event(event)
