"""
Data models cho Auto-Click Tool.
Định nghĩa cấu trúc dữ liệu cho các sự kiện chuột và recording.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from enum import Enum


class EventType(str, Enum):
    """Loại sự kiện chuột."""
    MOVE = "move"
    CLICK = "click"
    SCROLL = "scroll"


class ButtonType(str, Enum):
    """Loại nút chuột."""
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"
    NONE = "none"


@dataclass
class MouseEvent:
    """Một sự kiện chuột đơn lẻ."""
    timestamp: float          # Thời gian tương đối (giây) từ event đầu tiên
    event_type: str           # move, click, scroll
    x: int                    # Tọa độ X
    y: int                    # Tọa độ Y
    button: str = "none"      # left, right, middle
    pressed: bool = False     # True = nhấn, False = thả
    scroll_dx: int = 0        # Cuộn ngang
    scroll_dy: int = 0        # Cuộn dọc

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'MouseEvent':
        return cls(**data)


@dataclass
class Recording:
    """Một bản ghi chứa danh sách sự kiện chuột."""
    name: str = "Untitled"
    events: List[MouseEvent] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    screen_width: int = 1920
    screen_height: int = 1080

    @property
    def duration(self) -> float:
        """Tổng thời lượng recording (giây)."""
        if not self.events:
            return 0.0
        return self.events[-1].timestamp

    @property
    def total_events(self) -> int:
        return len(self.events)

    @property
    def total_clicks(self) -> int:
        return sum(1 for e in self.events if e.event_type == EventType.CLICK and e.pressed)

    @property
    def total_moves(self) -> int:
        return sum(1 for e in self.events if e.event_type == EventType.MOVE)

    @property
    def total_scrolls(self) -> int:
        return sum(1 for e in self.events if e.event_type == EventType.SCROLL)

    def add_event(self, event: MouseEvent):
        self.events.append(event)

    def clear(self):
        self.events.clear()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "created_at": self.created_at,
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "duration": self.duration,
            "total_events": self.total_events,
            "total_clicks": self.total_clicks,
            "events": [e.to_dict() for e in self.events]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Recording':
        events = [MouseEvent.from_dict(e) for e in data.get("events", [])]
        return cls(
            name=data.get("name", "Untitled"),
            events=events,
            created_at=data.get("created_at", ""),
            screen_width=data.get("screen_width", 1920),
            screen_height=data.get("screen_height", 1080),
        )

    def save_to_file(self, filepath: str):
        """Lưu recording ra file JSON."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'Recording':
        """Tải recording từ file JSON."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
