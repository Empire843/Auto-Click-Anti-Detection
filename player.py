"""
Mouse Player Module - Phiên bản Anti-Detection.
Phát lại sự kiện chuột với humanization để tránh bị phát hiện.
"""

import time
import threading
from typing import Callable, Optional

from models import MouseEvent, Recording, EventType, ButtonType
from humanizer import HumanizedMover, HumanizeSettings


class MousePlayer:
    """Phát lại sự kiện chuột với chuyển động giống người thật."""

    def __init__(self):
        self._recording: Optional[Recording] = None
        self._thread: Optional[threading.Thread] = None
        self._is_playing: bool = False
        self._is_paused: bool = False
        self._stop_flag: bool = False
        self._speed: float = 1.0
        self._loop_count: int = 1
        self._loop_interval: float = 0.0  # Khoảng cách giữa các lần lặp (giây)
        self._current_loop: int = 0
        self._current_event_index: int = 0
        self._waiting_interval: bool = False  # Đang chờ interval

        # Humanizer
        self.humanize_settings = HumanizeSettings()
        self._mover: Optional[HumanizedMover] = None

        # Callbacks
        self.on_event_played: Optional[Callable[[int, MouseEvent], None]] = None
        self.on_loop_completed: Optional[Callable[[int], None]] = None
        self.on_playback_finished: Optional[Callable[[], None]] = None
        self.on_playback_started: Optional[Callable[[], None]] = None

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    @property
    def speed(self) -> float:
        return self._speed

    @speed.setter
    def speed(self, value: float):
        self._speed = max(0.1, min(10.0, value))

    @property
    def loop_count(self) -> int:
        return self._loop_count

    @loop_count.setter
    def loop_count(self, value: int):
        self._loop_count = max(0, value)

    @property
    def loop_interval(self) -> float:
        return self._loop_interval

    @loop_interval.setter
    def loop_interval(self, value: float):
        self._loop_interval = max(0.0, value)

    @property
    def is_waiting_interval(self) -> bool:
        return self._waiting_interval

    @property
    def current_loop(self) -> int:
        return self._current_loop

    @property
    def current_event_index(self) -> int:
        return self._current_event_index

    @property
    def progress(self) -> float:
        if not self._recording or not self._recording.events:
            return 0.0
        return self._current_event_index / len(self._recording.events)

    def start(self, recording: Recording):
        if self._is_playing:
            return
        if not recording or not recording.events:
            return

        self._recording = recording
        self._stop_flag = False
        self._is_playing = True
        self._is_paused = False
        self._current_loop = 0
        self._current_event_index = 0

        # Khởi tạo humanizer
        self._mover = HumanizedMover(self.humanize_settings)
        # Set vị trí ban đầu từ event đầu tiên
        first = recording.events[0]
        self._mover.update_position(first.x, first.y)

        self._thread = threading.Thread(target=self._play_loop, daemon=True)
        self._thread.start()

        if self.on_playback_started:
            self.on_playback_started()

    def stop(self):
        self._stop_flag = True
        self._is_paused = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._is_playing = False
        self._thread = None

    def pause(self):
        if self._is_playing:
            self._is_paused = True

    def resume(self):
        if self._is_playing:
            self._is_paused = False

    def toggle_pause(self):
        if self._is_paused:
            self.resume()
        else:
            self.pause()

    def _play_loop(self):
        try:
            import random
            while not self._stop_flag:
                self._current_loop += 1
                self._waiting_interval = False
                self._play_once()

                if self._stop_flag:
                    break

                if self.on_loop_completed:
                    self.on_loop_completed(self._current_loop)

                if self._loop_count > 0 and self._current_loop >= self._loop_count:
                    break

                # Chờ interval giữa các lần lặp
                if self._loop_interval > 0:
                    self._waiting_interval = True
                    # Thêm jitter ±10% để tự nhiên hơn
                    jitter = random.uniform(0.9, 1.1)
                    wait_time = self._loop_interval * jitter
                    self._interruptible_sleep(wait_time)
                    self._waiting_interval = False
                else:
                    # Delay ngẫu nhiên nhỏ nếu không có interval
                    time.sleep(random.uniform(0.2, 0.5))

        except Exception as e:
            print(f"[Player] Lỗi phát lại: {e}")
        finally:
            self._is_playing = False
            if self.on_playback_finished:
                self.on_playback_finished()

    def _play_once(self):
        if not self._recording or not self._mover:
            return

        events = self._recording.events
        self._current_event_index = 0
        n = len(events)
        i = 0

        while i < n:
            if self._stop_flag:
                return

            while self._is_paused and not self._stop_flag:
                time.sleep(0.05)

            if self._stop_flag:
                return

            event = events[i]
            self._current_event_index = i

            # Tính delay từ event trước
            if i > 0:
                delay = (event.timestamp - events[i - 1].timestamp) / self._speed
            else:
                delay = 0

            if event.event_type == EventType.MOVE and delay >= 0:
                # === Gộp move events liên tiếp có delay ngắn ===
                # Tìm chuỗi move events liên tiếp
                total_duration = delay
                last_move_idx = i

                # Ngưỡng: nếu delay mỗi step < 5ms thì gộp lại
                min_move_duration = 0.005
                j = i + 1
                while j < n and events[j].event_type == EventType.MOVE:
                    next_delay = (events[j].timestamp - events[j - 1].timestamp) / self._speed
                    if next_delay < min_move_duration and total_duration + next_delay < 0.1:
                        total_duration += next_delay
                        last_move_idx = j
                        j += 1
                    else:
                        break

                # Di chuyển đến vị trí cuối cùng của chuỗi
                target_event = events[last_move_idx]
                actual_duration = max(total_duration, 0.006)
                self._execute_event(target_event, actual_duration)

                if self.on_event_played:
                    self.on_event_played(last_move_idx, target_event)

                i = last_move_idx + 1
                continue

            else:
                # Non-move events: sleep rồi execute
                if delay > 0:
                    self._interruptible_sleep(delay)

            if self._stop_flag:
                return

            self._execute_event(event, 0)

            if self.on_event_played:
                self.on_event_played(i, event)

            i += 1

    def _interruptible_sleep(self, duration: float):
        """Sleep có thể bị interrupt bởi stop flag."""
        end_time = time.time() + duration
        while time.time() < end_time and not self._stop_flag:
            time.sleep(min(0.01, end_time - time.time()))

    def _execute_event(self, event: MouseEvent, duration: float = 0):
        """Thực thi event với humanization."""
        try:
            if event.event_type == EventType.MOVE:
                self._mover.move_to(event.x, event.y, duration)

            elif event.event_type == EventType.CLICK:
                # Di chuyển đến vị trí click trước
                self._mover.move_to(event.x, event.y, min(duration, 0.05))
                self._mover.click(event.x, event.y, event.button, event.pressed)

            elif event.event_type == EventType.SCROLL:
                self._mover.move_to(event.x, event.y, min(duration, 0.03))
                self._mover.scroll(event.scroll_dy)

        except Exception as e:
            print(f"[Player] Lỗi event: {e}")
            if "FailSafe" in str(e):
                self._stop_flag = True
