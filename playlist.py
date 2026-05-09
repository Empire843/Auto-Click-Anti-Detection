"""
Playlist Controller - Manage and run multiple recordings sequentially.
"""

import time
import threading
from typing import Callable, List, Optional

from models import Recording
from player import MousePlayer
from humanizer import HumanizeSettings


class PlaylistItem:
    """A single item in the playlist."""
    def __init__(self, filepath: str, recording: Recording):
        self.filepath = filepath
        self.recording = recording

    @property
    def name(self) -> str:
        return self.recording.name or self.filepath.split("\\")[-1].split("/")[-1]

    @property
    def event_count(self) -> int:
        return self.recording.total_events

    @property
    def duration(self) -> float:
        return self.recording.duration

    @property
    def click_count(self) -> int:
        return self.recording.total_clicks


class PlaylistController:
    """Controls sequential execution of a list of recordings."""

    def __init__(self):
        self.items: List[PlaylistItem] = []
        self._player = MousePlayer()
        self._thread: Optional[threading.Thread] = None
        self._is_running: bool = False
        self._stop_flag: bool = False
        self._current_index: int = 0
        self._current_cycle: int = 0
        self._total_cycles: int = 1   # 0 = infinite
        self._interval: float = 0.0    # Rest between recordings (seconds)
        self._waiting: bool = False

        # Callbacks
        self.on_item_started: Optional[Callable[[int, PlaylistItem], None]] = None
        self.on_item_finished: Optional[Callable[[int, PlaylistItem], None]] = None
        self.on_cycle_completed: Optional[Callable[[int], None]] = None
        self.on_playlist_finished: Optional[Callable[[], None]] = None
        self.on_progress: Optional[Callable[[float], None]] = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_waiting(self) -> bool:
        return self._waiting

    @property
    def current_index(self) -> int:
        return self._current_index

    @property
    def current_cycle(self) -> int:
        return self._current_cycle

    @property
    def total_cycles(self) -> int:
        return self._total_cycles

    @property
    def item_count(self) -> int:
        return len(self.items)

    @property
    def player(self) -> MousePlayer:
        return self._player

    def add_item(self, filepath: str, recording: Recording) -> int:
        """Add recording to playlist. Returns index."""
        item = PlaylistItem(filepath, recording)
        self.items.append(item)
        return len(self.items) - 1

    def remove_item(self, index: int):
        if 0 <= index < len(self.items):
            self.items.pop(index)

    def move_up(self, index: int):
        if 0 < index < len(self.items):
            self.items[index - 1], self.items[index] = self.items[index], self.items[index - 1]

    def move_down(self, index: int):
        if 0 <= index < len(self.items) - 1:
            self.items[index], self.items[index + 1] = self.items[index + 1], self.items[index]

    def clear(self):
        self.items.clear()

    def start(self, speed: float = 1.0, total_cycles: int = 1, interval: float = 0.0,
              humanize_settings: HumanizeSettings = None):
        """Start running the playlist."""
        if self._is_running or not self.items:
            return

        self._stop_flag = False
        self._is_running = True
        self._current_index = 0
        self._current_cycle = 0
        self._total_cycles = total_cycles
        self._interval = interval

        self._player.speed = speed
        self._player.loop_count = 1  # Each recording runs once
        self._player.loop_interval = 0
        if humanize_settings:
            self._player.humanize_settings = humanize_settings

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the playlist."""
        self._stop_flag = True
        self._player.stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self._is_running = False
        self._thread = None

    def _run_loop(self):
        """Main playlist execution loop."""
        import random
        try:
            while not self._stop_flag:
                self._current_cycle += 1

                for idx, item in enumerate(self.items):
                    if self._stop_flag:
                        return

                    self._current_index = idx
                    self._waiting = False

                    if self.on_item_started:
                        self.on_item_started(idx, item)

                    # Play this recording
                    self._play_single(item.recording)

                    if self._stop_flag:
                        return

                    if self.on_item_finished:
                        self.on_item_finished(idx, item)

                    # Rest between recordings
                    if idx < len(self.items) - 1 and self._interval > 0:
                        self._waiting = True
                        jitter = random.uniform(0.9, 1.1)
                        self._interruptible_sleep(self._interval * jitter)
                        self._waiting = False

                if self._stop_flag:
                    return

                if self.on_cycle_completed:
                    self.on_cycle_completed(self._current_cycle)

                # Check completion
                if self._total_cycles > 0 and self._current_cycle >= self._total_cycles:
                    break

                # Rest between cycles
                if self._interval > 0:
                    self._waiting = True
                    jitter = random.uniform(0.9, 1.1)
                    self._interruptible_sleep(self._interval * jitter)
                    self._waiting = False

        except Exception as e:
            print(f"[Playlist] Error: {e}")
        finally:
            self._is_running = False
            self._waiting = False
            if self.on_playlist_finished:
                self.on_playlist_finished()

    def _play_single(self, recording: Recording):
        """Play a single recording and wait for completion."""
        done_event = threading.Event()

        original_callback = self._player.on_playback_finished
        self._player.on_playback_finished = lambda: done_event.set()

        self._player.start(recording)

        # Wait for player to finish
        while not done_event.is_set() and not self._stop_flag:
            done_event.wait(timeout=0.1)

        self._player.on_playback_finished = original_callback

        if self._stop_flag:
            self._player.stop()

    def _interruptible_sleep(self, duration: float):
        end_time = time.time() + duration
        while time.time() < end_time and not self._stop_flag:
            time.sleep(min(0.05, end_time - time.time()))
