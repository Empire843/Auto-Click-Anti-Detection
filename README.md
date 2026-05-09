# ⚡ Auto-Click Tool — Anti-Detection

A mouse macro recorder & player with built-in **anti-detection** technology that mimics real human behavior. Designed for automating repetitive tasks on Windows while bypassing browser-based anti-bot systems.

---

## ✨ Key Features

### 🎬 Record & Replay
- **Record** all mouse actions: movement, clicks (left/right/middle), scrolling
- **Replay** with adjustable speed (0.1x → 5.0x)
- **Loop** multiple times (or infinitely) with configurable rest intervals
- **Visualize** mouse trajectory in real-time on an interactive canvas

### 📁 Playlist Controller
- Manage and run **multiple recordings** sequentially
- Reorder (up/down), add/remove recordings
- **Run All** — execute the entire playlist with custom loop cycles and interval delays

### 🛡 Anti-Detection Engine
| Technique | Description |
|---|---|
| **Win32 SendInput** | Hardware-level mouse events that produce `isTrusted=true` in browsers |
| **Bezier Curves** | Natural curved mouse movement instead of straight lines |
| **Gaussian Noise** | Random position & timing perturbations |
| **Speed Profile** | Natural acceleration/deceleration (ease in-out cubic) |
| **Micro-tremor** | Subtle hand tremor simulation mimicking real human movement |
| **Variable Click Duration** | Randomized press/release timing for realistic clicks |

---

## 🖥 Interface

- Modern **dark mode** UI built with **CustomTkinter**
- Hotkeys: `F6` (Record), `F7` (Play), `F8` (Emergency Stop)
- Real-time stats: event count, clicks, duration
- Integrated event log & playlist manager

---

## 📦 Installation

### Requirements
- Python 3.10+
- Windows 10/11

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run from source

```bash
python main.py
```

### Build as standalone .exe

```bash
pip install pyinstaller
pyinstaller AutoClick.spec --noconfirm
```

The `.exe` will be generated in the `dist/` folder.

---

## 🏗 Project Structure

```
auto-click/
├── main.py             # Entry point
├── gui.py              # CustomTkinter UI
├── recorder.py         # Mouse event recorder (pynput)
├── player.py           # Mouse event player
├── playlist.py         # Playlist controller — sequential multi-recording execution
├── humanizer.py        # Anti-detection engine (Bezier, SendInput, Noise...)
├── models.py           # Data models: MouseEvent, Recording
├── utils.py            # Utilities: config management, formatting, paths
├── requirements.txt    # Dependencies
├── AutoClick.spec      # PyInstaller build config
└── recordings/         # Default directory for saved recordings (.json)
```

---

## 🎮 Usage

1. **Record**: Press `F6` or click "Start Recording" → perform mouse actions → press `F6` again to stop
2. **Save**: Click "Save" to export as a `.json` file
3. **Replay**: Press `F7` or click "Play" — adjust speed, loop count, and rest interval as needed
4. **Playlist**: Switch to the "Playlist" tab → add multiple recordings → click "Run All"
5. **Emergency Stop**: Press `F8` at any time to immediately halt all activity

---

## ⚙️ Anti-Detection Settings

All toggles are accessible directly from the UI:

- **Humanize movement** — Enable the full anti-detection pipeline
- **Win32 SendInput (HW)** — Use hardware-level API instead of pyautogui
- **Bezier curves** — Curved mouse paths
- **Micro-tremor** — Simulate natural hand tremor

---

## 📝 Recording Format

Recordings are stored as JSON files:

```json
{
  "name": "Untitled",
  "created_at": "2026-05-09 14:00:00",
  "screen_width": 1920,
  "screen_height": 1080,
  "duration": 5.23,
  "total_events": 342,
  "total_clicks": 8,
  "events": [
    {
      "timestamp": 0.0,
      "event_type": "move",
      "x": 500,
      "y": 300,
      "button": "none",
      "pressed": false,
      "scroll_dx": 0,
      "scroll_dy": 0
    }
  ]
}
```

---

## 📄 License

MIT License — Free for personal and commercial use.
