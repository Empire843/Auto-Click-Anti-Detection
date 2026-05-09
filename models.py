"""
Data models for Auto-Click Tool.
Defines data structures for mouse events and recordings.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from enum import Enum


class EventType(str, Enum):
    """Mouse event type."""
    MOVE = "move"
    CLICK = "click"
    SCROLL = "scroll"


class ButtonType(str, Enum):
    """Mouse button type."""
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"
    NONE = "none"


@dataclass
class MouseEvent:
    """A single mouse event."""
    timestamp: float          # Relative time (seconds) from first event
    event_type: str           # move, click, scroll
    x: int                    # X coordinate
    y: int                    # Y coordinate
    button: str = "none"      # left, right, middle
    pressed: bool = False     # True = press, False = release
    scroll_dx: int = 0        # Horizontal scroll
    scroll_dy: int = 0        # Vertical scroll

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'MouseEvent':
        return cls(**data)


@dataclass
class Recording:
    """A recording containing a list of mouse events."""
    name: str = "Untitled"
    events: List[MouseEvent] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    screen_width: int = 1920
    screen_height: int = 1080

    @property
    def duration(self) -> float:
        """Total recording duration (seconds)."""
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
        """Save recording to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'Recording':
        """Load recording from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
