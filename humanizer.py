"""
Humanizer Module - Anti-Detection cho Auto-Click Tool.

Kỹ thuật chống phát hiện:
1. Win32 SendInput - Hardware-level mouse events (isTrusted=true trong JS)
2. Bezier curves - Chuyển động chuột theo đường cong tự nhiên
3. Gaussian noise - Thêm nhiễu vị trí + thời gian
4. Speed profile - Tăng/giảm tốc tự nhiên (ease in/out)
5. Micro-tremor - Rung nhẹ mô phỏng tay người thật
6. Variable click duration - Thời gian nhấn/thả không đều
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
    """Gửi input events qua Win32 API."""
    n = len(inputs)
    arr = (INPUT * n)(*inputs)
    ctypes.windll.user32.SendInput(n, arr, ctypes.sizeof(INPUT))


def _get_screen_size():
    """Lấy kích thước màn hình."""
    w = ctypes.windll.user32.GetSystemMetrics(0)
    h = ctypes.windll.user32.GetSystemMetrics(1)
    return w, h


def _to_absolute(x: int, y: int) -> Tuple[int, int]:
    """Chuyển tọa độ pixel sang tọa độ absolute (0-65535)."""
    sw, sh = _get_screen_size()
    abs_x = int(x * 65536 / sw)
    abs_y = int(y * 65536 / sh)
    return abs_x, abs_y


def win32_move_to(x: int, y: int):
    """Di chuyển chuột bằng SendInput (hardware-level)."""
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
    """Nhấn nút chuột bằng SendInput."""
    flag_map = {"left": MOUSEEVENTF_LEFTDOWN, "right": MOUSEEVENTF_RIGHTDOWN, "middle": MOUSEEVENTF_MIDDLEDOWN}
    flag = flag_map.get(button, MOUSEEVENTF_LEFTDOWN)
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi.dwFlags = flag
    inp.union.mi.time = 0
    inp.union.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    _send_input([inp])


def win32_mouse_up(button: str = "left"):
    """Thả nút chuột bằng SendInput."""
    flag_map = {"left": MOUSEEVENTF_LEFTUP, "right": MOUSEEVENTF_RIGHTUP, "middle": MOUSEEVENTF_MIDDLEUP}
    flag = flag_map.get(button, MOUSEEVENTF_LEFTUP)
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi.dwFlags = flag
    inp.union.mi.time = 0
    inp.union.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    _send_input([inp])


def win32_scroll(dy: int):
    """Cuộn chuột bằng SendInput."""
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi.mouseData = ctypes.wintypes.DWORD(dy * 120)
    inp.union.mi.dwFlags = MOUSEEVENTF_WHEEL
    inp.union.mi.time = 0
    inp.union.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    _send_input([inp])


# ============================================================
# Bezier Curve - Đường cong tự nhiên
# ============================================================

def _bezier_point(t: float, points: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Tính điểm trên đường Bezier bậc N tại t (0..1)."""
    n = len(points) - 1
    x, y = 0.0, 0.0
    for i, (px, py) in enumerate(points):
        coeff = _binomial(n, i) * (t ** i) * ((1 - t) ** (n - i))
        x += coeff * px
        y += coeff * py
    return x, y


def _binomial(n: int, k: int) -> int:
    """Hệ số nhị thức."""
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
    Tạo đường cong Bezier từ start đến end.
    curvature: mức độ cong (0 = thẳng, 1 = rất cong)
    """
    sx, sy = start
    ex, ey = end
    dist = math.sqrt((ex - sx) ** 2 + (ey - sy) ** 2)

    if dist < 3:
        return [end]

    # Tạo 1-2 control points ngẫu nhiên
    num_controls = 1 if dist < 200 else 2
    controls = []

    for i in range(num_controls):
        t = (i + 1) / (num_controls + 1)
        # Điểm trung gian
        mx = sx + (ex - sx) * t
        my = sy + (ey - sy) * t
        # Offset ngẫu nhiên vuông góc với đường thẳng
        offset = dist * curvature * random.gauss(0, 0.5)
        angle = math.atan2(ey - sy, ex - sx) + math.pi / 2
        cx = mx + offset * math.cos(angle)
        cy = my + offset * math.sin(angle)
        controls.append((cx, cy))

    # Bezier points: start + controls + end
    bezier_pts = [(float(sx), float(sy))] + controls + [(float(ex), float(ey))]

    # Sample points trên đường Bezier
    path = []
    for i in range(num_points):
        t = i / max(num_points - 1, 1)
        bx, by = _bezier_point(t, bezier_pts)
        path.append((int(round(bx)), int(round(by))))

    return path


# ============================================================
# Speed Profile - Tăng/giảm tốc tự nhiên
# ============================================================

def ease_in_out(t: float) -> float:
    """Ease in-out cubic: chậm → nhanh → chậm."""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - (-2 * t + 2) ** 3 / 2


def generate_time_points(num_points: int, total_duration: float) -> List[float]:
    """
    Tạo danh sách thời gian với speed profile tự nhiên.
    Kết quả: delay giữa mỗi điểm liên tiếp.
    """
    if num_points <= 1:
        return [total_duration]

    delays = []
    for i in range(num_points - 1):
        t = i / (num_points - 1)
        # Ease in-out: chậm ở đầu và cuối
        speed_factor = 0.3 + 0.7 * (1 - abs(ease_in_out(t) * 2 - 1))
        # Thêm jitter ngẫu nhiên ±15%
        jitter = random.gauss(1.0, 0.08)
        delay = (total_duration / num_points) * speed_factor * jitter
        delays.append(max(0.001, delay))

    # Normalize để tổng = total_duration
    total = sum(delays)
    if total > 0:
        scale = total_duration / total
        delays = [d * scale for d in delays]

    return delays


# ============================================================
# Noise & Micro-tremor
# ============================================================

def add_position_noise(x: int, y: int, intensity: float = 1.0) -> Tuple[int, int]:
    """Thêm nhiễu Gaussian vào vị trí (mô phỏng rung tay)."""
    noise_x = int(random.gauss(0, 0.8 * intensity))
    noise_y = int(random.gauss(0, 0.8 * intensity))
    return x + noise_x, y + noise_y


def add_timing_noise(delay: float, intensity: float = 1.0) -> float:
    """Thêm nhiễu vào thời gian chờ."""
    noise = random.gauss(0, delay * 0.05 * intensity)
    return max(0.001, delay + noise)


def random_click_hold_duration() -> float:
    """Thời gian giữ nút chuột (50-150ms, phân phối Gaussian)."""
    return max(0.03, random.gauss(0.085, 0.025))


# ============================================================
# HumanizedMover - Kết hợp tất cả kỹ thuật
# ============================================================

@dataclass
class HumanizeSettings:
    """Cài đặt humanization."""
    enabled: bool = True           # Bật/tắt humanization
    bezier_curvature: float = 0.25  # Mức độ cong (0-1)
    position_noise: float = 1.0    # Cường độ nhiễu vị trí (0-3)
    timing_noise: float = 1.0     # Cường độ nhiễu thời gian (0-3)
    micro_tremor: bool = True      # Bật rung nhẹ
    use_win32: bool = True         # Dùng SendInput thay vì pyautogui
    move_steps_min: int = 20       # Số bước di chuyển tối thiểu
    move_steps_max: int = 80       # Số bước di chuyển tối đa


class HumanizedMover:
    """Di chuyển chuột giống người thật."""

    def __init__(self, settings: HumanizeSettings = None):
        self.settings = settings or HumanizeSettings()
        self._last_x = 0
        self._last_y = 0

    # Thời gian sleep tối thiểu mỗi bước (giây) - Windows timer resolution
    MIN_STEP_DURATION = 0.002  # 2ms

    def move_to(self, x: int, y: int, duration: float = 0.0):
        """
        Di chuyển chuột đến (x, y) theo đường cong tự nhiên.
        duration: thời gian di chuyển (0 = instant)
        Tự động điều chỉnh số bước Bezier theo duration để tránh nhảy chuột.
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
            # Quá gần → di chuyển trực tiếp, không cần interpolate
            if self.settings.use_win32:
                win32_move_to(x, y)
            else:
                import pyautogui
                pyautogui.moveTo(x, y, _pause=False)
            self._last_x, self._last_y = x, y
            return

        # === Tính số bước dựa trên CẢ khoảng cách VÀ thời gian ===
        # Bước theo khoảng cách (mỗi ~8px 1 bước)
        steps_by_dist = int(dist / 8)
        steps_by_dist = max(self.settings.move_steps_min, min(self.settings.move_steps_max, steps_by_dist))

        # Bước tối đa theo thời gian (đảm bảo mỗi step ≥ 2ms)
        if duration > 0:
            steps_by_time = int(duration / self.MIN_STEP_DURATION)
        else:
            steps_by_time = 5  # instant move

        # Lấy giá trị nhỏ hơn để đảm bảo mượt
        steps = max(3, min(steps_by_dist, steps_by_time))

        # Đảm bảo duration tối thiểu cho interpolation
        actual_duration = max(duration, steps * self.MIN_STEP_DURATION)

        # Tạo đường Bezier
        path = generate_bezier_path(start, end, steps, self.settings.bezier_curvature)

        # Tạo timing tự nhiên
        delays = generate_time_points(len(path), actual_duration)

        # Di chuyển theo path
        for i, (px, py) in enumerate(path):
            # Thêm micro-tremor (mỗi 3 bước)
            if self.settings.micro_tremor and i % 3 == 0:
                px, py = add_position_noise(px, py, self.settings.position_noise * 0.5)

            if self.settings.use_win32:
                win32_move_to(px, py)
            else:
                import pyautogui
                pyautogui.moveTo(px, py, _pause=False)

            # Delay với noise
            if i < len(delays):
                delay = add_timing_noise(delays[i], self.settings.timing_noise)
                if delay >= self.MIN_STEP_DURATION:
                    time.sleep(delay)

        self._last_x, self._last_y = x, y

    def click(self, x: int, y: int, button: str = "left", pressed: bool = True):
        """Click chuột tại vị trí."""
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
        """Cuộn chuột."""
        if self.settings.use_win32:
            win32_scroll(dy)
        else:
            import pyautogui
            pyautogui.scroll(dy, _pause=False)

    def update_position(self, x: int, y: int):
        """Cập nhật vị trí hiện tại (không di chuyển)."""
        self._last_x = x
        self._last_y = y
