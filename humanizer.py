"""
Humanizer Module - Anti-Detection for Auto-Click Tool.

Anti-detection techniques:
1. Win32 SendInput - Hardware-level mouse events (isTrusted=true in JS)
2. Bezier curves - Natural curved mouse movement
3. Gaussian noise - Position + timing perturbation
4. Speed profile - Natural acceleration/deceleration (ease in/out)
5. Micro-tremor - Subtle tremor simulating real human hand
6. Variable click duration - Non-uniform press/release timing
"""

import ctypes
import ctypes.wintypes
import math
import random
import time
from dataclasses import dataclass
from typing import List, Tuple

# ============================================================
# Win32 SendInput API - Hardware-level mouse simulation
# ============================================================

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.wintypes.LONG),
        ("dy", ctypes.wintypes.LONG),
        ("mouseData", ctypes.wintypes.DWORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.wintypes.DWORD),
        ("union", INPUT_UNION),
    ]


def _send_input(inputs):
    """Send input events via Win32 API."""
    n = len(inputs)
    arr = (INPUT * n)(*inputs)
    ctypes.windll.user32.SendInput(n, arr, ctypes.sizeof(INPUT))


def _get_screen_size():
    """Get screen dimensions."""
    w = ctypes.windll.user32.GetSystemMetrics(0)
    h = ctypes.windll.user32.GetSystemMetrics(1)
    return w, h


def _to_absolute(x: int, y: int) -> Tuple[int, int]:
    """Convert pixel coordinates to absolute coordinates (0-65535)."""
    sw, sh = _get_screen_size()
    abs_x = int(x * 65536 / sw)
    abs_y = int(y * 65536 / sh)
    return abs_x, abs_y


def win32_move_to(x: int, y: int):
    """Move mouse using SendInput (hardware-level)."""
    abs_x, abs_y = _to_absolute(x, y)
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi.dx = abs_x
    inp.union.mi.dy = abs_y
    inp.union.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
    inp.union.mi.time = 0
    inp.union.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    _send_input([inp])


def win32_mouse_down(button: str = "left"):
    """Press mouse button using SendInput."""
    flag_map = {"left": MOUSEEVENTF_LEFTDOWN, "right": MOUSEEVENTF_RIGHTDOWN, "middle": MOUSEEVENTF_MIDDLEDOWN}
    flag = flag_map.get(button, MOUSEEVENTF_LEFTDOWN)
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi.dwFlags = flag
    inp.union.mi.time = 0
    inp.union.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    _send_input([inp])


def win32_mouse_up(button: str = "left"):
    """Release mouse button using SendInput."""
    flag_map = {"left": MOUSEEVENTF_LEFTUP, "right": MOUSEEVENTF_RIGHTUP, "middle": MOUSEEVENTF_MIDDLEUP}
    flag = flag_map.get(button, MOUSEEVENTF_LEFTUP)
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi.dwFlags = flag
    inp.union.mi.time = 0
    inp.union.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    _send_input([inp])


def win32_scroll(dy: int):
    """Scroll mouse using SendInput."""
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi.mouseData = ctypes.wintypes.DWORD(dy * 120)
    inp.union.mi.dwFlags = MOUSEEVENTF_WHEEL
    inp.union.mi.time = 0
    inp.union.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    _send_input([inp])


# ============================================================
# Bezier Curve - Natural curved paths
# ============================================================

def _bezier_point(t: float, points: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Calculate point on N-degree Bezier curve at t (0..1)."""
    n = len(points) - 1
    x, y = 0.0, 0.0
    for i, (px, py) in enumerate(points):
        coeff = _binomial(n, i) * (t ** i) * ((1 - t) ** (n - i))
        x += coeff * px
        y += coeff * py
    return x, y


def _binomial(n: int, k: int) -> int:
    """Binomial coefficient."""
    if k < 0 or k > n:
        return 0
    result = 1
    for i in range(min(k, n - k)):
        result = result * (n - i) // (i + 1)
    return result


def generate_bezier_path(
    start: Tuple[int, int],
    end: Tuple[int, int],
    num_points: int = 50,
    curvature: float = 0.3
) -> List[Tuple[int, int]]:
    """
    Generate Bezier curve from start to end.
    curvature: curve intensity (0 = straight, 1 = very curved)
    """
    sx, sy = start
    ex, ey = end
    dist = math.sqrt((ex - sx) ** 2 + (ey - sy) ** 2)

    if dist < 3:
        return [end]

    # Create 1-2 random control points
    num_controls = 1 if dist < 200 else 2
    controls = []

    for i in range(num_controls):
        t = (i + 1) / (num_controls + 1)
        # Intermediate point
        mx = sx + (ex - sx) * t
        my = sy + (ey - sy) * t
        # Random offset perpendicular to the line
        offset = dist * curvature * random.gauss(0, 0.5)
        angle = math.atan2(ey - sy, ex - sx) + math.pi / 2
        cx = mx + offset * math.cos(angle)
        cy = my + offset * math.sin(angle)
        controls.append((cx, cy))

    # Bezier points: start + controls + end
    bezier_pts = [(float(sx), float(sy))] + controls + [(float(ex), float(ey))]

    # Sample points on the Bezier curve
    path = []
    for i in range(num_points):
        t = i / max(num_points - 1, 1)
        bx, by = _bezier_point(t, bezier_pts)
        path.append((int(round(bx)), int(round(by))))

    return path


# ============================================================
# Speed Profile - Natural acceleration/deceleration
# ============================================================

def ease_in_out(t: float) -> float:
    """Ease in-out cubic: slow -> fast -> slow."""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - (-2 * t + 2) ** 3 / 2


def generate_time_points(num_points: int, total_duration: float) -> List[float]:
    """
    Generate time points with natural speed profile.
    Result: delay between each consecutive pair of points.
    """
    if num_points <= 1:
        return [total_duration]

    delays = []
    for i in range(num_points - 1):
        t = i / (num_points - 1)
        # Ease in-out: slow at start and end
        speed_factor = 0.3 + 0.7 * (1 - abs(ease_in_out(t) * 2 - 1))
        # Add random jitter +/-15%
        jitter = random.gauss(1.0, 0.08)
        delay = (total_duration / num_points) * speed_factor * jitter
        delays.append(max(0.001, delay))

    # Normalize so total = total_duration
    total = sum(delays)
    if total > 0:
        scale = total_duration / total
        delays = [d * scale for d in delays]

    return delays


# ============================================================
# Noise & Micro-tremor
# ============================================================

def add_position_noise(x: int, y: int, intensity: float = 1.0) -> Tuple[int, int]:
    """Add Gaussian noise to position (simulates hand tremor)."""
    noise_x = int(random.gauss(0, 0.8 * intensity))
    noise_y = int(random.gauss(0, 0.8 * intensity))
    return x + noise_x, y + noise_y


def add_timing_noise(delay: float, intensity: float = 1.0) -> float:
    """Add noise to timing delay."""
    noise = random.gauss(0, delay * 0.05 * intensity)
    return max(0.001, delay + noise)


def random_click_hold_duration() -> float:
    """Mouse button hold duration (50-150ms, Gaussian distribution)."""
    return max(0.03, random.gauss(0.085, 0.025))


# ============================================================
# HumanizedMover - Combines all techniques
# ============================================================

@dataclass
class HumanizeSettings:
    """Humanization settings."""
    enabled: bool = True           # Enable/disable humanization
    bezier_curvature: float = 0.25  # Curve intensity (0-1)
    position_noise: float = 1.0    # Position noise intensity (0-3)
    timing_noise: float = 1.0     # Timing noise intensity (0-3)
    micro_tremor: bool = True      # Enable subtle tremor
    use_win32: bool = True         # Use SendInput instead of pyautogui
    move_steps_min: int = 20       # Minimum movement steps
    move_steps_max: int = 80       # Maximum movement steps


class HumanizedMover:
    """Moves mouse in a human-like manner."""

    def __init__(self, settings: HumanizeSettings = None):
        self.settings = settings or HumanizeSettings()
        self._last_x = 0
        self._last_y = 0

    # Minimum sleep per step (seconds) - Windows timer resolution
    MIN_STEP_DURATION = 0.002  # 2ms

    def move_to(self, x: int, y: int, duration: float = 0.0):
        """
        Move mouse to (x, y) along a natural curve.
        duration: movement time (0 = instant)
        Automatically adjusts Bezier steps based on duration to prevent mouse jumping.
        """
        if not self.settings.enabled:
            if self.settings.use_win32:
                win32_move_to(x, y)
            else:
                import pyautogui
                pyautogui.moveTo(x, y, _pause=False)
            self._last_x, self._last_y = x, y
            return

        start = (self._last_x, self._last_y)
        end = (x, y)

        dist = math.sqrt((x - start[0]) ** 2 + (y - start[1]) ** 2)

        if dist < 2:
            # Too close - move directly, no interpolation needed
            if self.settings.use_win32:
                win32_move_to(x, y)
            else:
                import pyautogui
                pyautogui.moveTo(x, y, _pause=False)
            self._last_x, self._last_y = x, y
            return

        # === Calculate steps based on BOTH distance AND time ===
        # Steps by distance (1 step per ~8px)
        steps_by_dist = int(dist / 8)
        steps_by_dist = max(self.settings.move_steps_min, min(self.settings.move_steps_max, steps_by_dist))

        # Max steps by time (ensure each step >= 2ms)
        if duration > 0:
            steps_by_time = int(duration / self.MIN_STEP_DURATION)
        else:
            steps_by_time = 5  # instant move

        # Take smaller value to ensure smoothness
        steps = max(3, min(steps_by_dist, steps_by_time))

        # Ensure minimum duration for interpolation
        actual_duration = max(duration, steps * self.MIN_STEP_DURATION)

        # Generate Bezier path
        path = generate_bezier_path(start, end, steps, self.settings.bezier_curvature)

        # Generate natural timing
        delays = generate_time_points(len(path), actual_duration)

        # Move along path
        for i, (px, py) in enumerate(path):
            # Add micro-tremor (every 3 steps)
            if self.settings.micro_tremor and i % 3 == 0:
                px, py = add_position_noise(px, py, self.settings.position_noise * 0.5)

            if self.settings.use_win32:
                win32_move_to(px, py)
            else:
                import pyautogui
                pyautogui.moveTo(px, py, _pause=False)

            # Delay with noise
            if i < len(delays):
                delay = add_timing_noise(delays[i], self.settings.timing_noise)
                if delay >= self.MIN_STEP_DURATION:
                    time.sleep(delay)

        self._last_x, self._last_y = x, y

    def click(self, x: int, y: int, button: str = "left", pressed: bool = True):
        """Click mouse at position."""
        if self.settings.use_win32:
            if pressed:
                win32_mouse_down(button)
            else:
                win32_mouse_up(button)
        else:
            import pyautogui
            if pressed:
                pyautogui.mouseDown(x, y, button=button, _pause=False)
            else:
                pyautogui.mouseUp(x, y, button=button, _pause=False)

    def scroll(self, dy: int):
        """Scroll mouse."""
        if self.settings.use_win32:
            win32_scroll(dy)
        else:
            import pyautogui
            pyautogui.scroll(dy, _pause=False)

    def update_position(self, x: int, y: int):
        """Update current position (without moving)."""
        self._last_x = x
        self._last_y = y
