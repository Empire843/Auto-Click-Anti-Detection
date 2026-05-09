# ⚡ Auto-Click Tool — Anti-Detection

Công cụ ghi lại và phát lại thao tác chuột tự động, tích hợp công nghệ **chống phát hiện** tiên tiến giúp mô phỏng hành vi con người thật. Phù hợp cho tự động hóa tác vụ lặp lại trên Windows.

---

## ✨ Tính năng chính

### 🎬 Ghi & Phát lại
- **Ghi lại** mọi thao tác chuột: di chuyển, click (trái/phải/giữa), cuộn
- **Phát lại** với tốc độ tùy chỉnh (0.1x → 5.0x)
- **Lặp lại** nhiều lần (hoặc vô hạn) với khoảng nghỉ giữa các lần
- **Hiển thị quỹ đạo** chuột trực quan trên canvas

### 📁 Playlist Controller
- Quản lý và chạy tuần tự **nhiều bản ghi** khác nhau
- Sắp xếp thứ tự (lên/xuống), thêm/xóa bản ghi
- **Run All** — chạy toàn bộ playlist với cấu hình vòng lặp và khoảng nghỉ riêng

### 🛡 Anti-Detection (Chống phát hiện)
| Kỹ thuật | Mô tả |
|---|---|
| **Win32 SendInput** | Gửi sự kiện chuột ở hardware-level, tạo ra `isTrusted=true` trong trình duyệt |
| **Bezier Curves** | Di chuyển chuột theo đường cong tự nhiên thay vì đường thẳng |
| **Gaussian Noise** | Thêm nhiễu ngẫu nhiên vào vị trí & thời gian |
| **Speed Profile** | Tăng/giảm tốc tự nhiên (ease in-out cubic) |
| **Micro-tremor** | Mô phỏng rung tay nhẹ của người thật |
| **Variable Click Duration** | Thời gian nhấn/thả nút chuột không đều |

---

## 🖥 Giao diện

- Giao diện dark mode hiện đại sử dụng **CustomTkinter**
- Phím tắt nhanh: `F6` (Ghi), `F7` (Phát), `F8` (Dừng khẩn cấp)
- Hiển thị thống kê real-time: số events, clicks, thời lượng
- Bảng sự kiện chi tiết & trình quản lý playlist tích hợp

---

## 📦 Cài đặt

### Yêu cầu
- Python 3.10+
- Windows 10/11

### Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Chạy từ source

```bash
python main.py
```

### Build thành file .exe

```bash
pip install pyinstaller
pyinstaller AutoClick.spec --noconfirm
```

File `.exe` sẽ nằm trong thư mục `dist/`.

---

## 🏗 Kiến trúc dự án

```
auto-click/
├── main.py             # Entry point
├── gui.py              # Giao diện CustomTkinter
├── recorder.py         # Module ghi thao tác chuột (pynput)
├── player.py           # Module phát lại thao tác
├── playlist.py         # Playlist controller — chạy tuần tự nhiều bản ghi
├── humanizer.py        # Anti-detection engine (Bezier, SendInput, Noise...)
├── models.py           # Data models: MouseEvent, Recording
├── utils.py            # Tiện ích: quản lý config, format, đường dẫn
├── requirements.txt    # Dependencies
├── AutoClick.spec      # PyInstaller build config
└── recordings/         # Thư mục mặc định lưu bản ghi (.json)
```

---

## 🎮 Hướng dẫn sử dụng

1. **Ghi lại thao tác**: Nhấn `F6` hoặc nút "Bắt đầu ghi" → thực hiện thao tác chuột → nhấn `F6` lần nữa để dừng
2. **Lưu bản ghi**: Nhấn "Lưu" để lưu thành file `.json`
3. **Phát lại**: Nhấn `F7` hoặc nút "Phát lại" — điều chỉnh tốc độ, số vòng lặp, khoảng nghỉ
4. **Playlist**: Chuyển sang tab "Playlist" → thêm nhiều bản ghi → nhấn "Run All"
5. **Dừng khẩn cấp**: Nhấn `F8` bất cứ lúc nào để dừng toàn bộ

---

## ⚙️ Cấu hình Anti-Detection

Tất cả có thể bật/tắt trực tiếp trên giao diện:

- **Humanize chuyển động** — Bật toàn bộ hệ thống chống phát hiện
- **Win32 SendInput (HW)** — Dùng hardware-level API thay vì pyautogui
- **Bezier curves** — Di chuyển chuột theo đường cong
- **Micro-tremor** — Mô phỏng rung tay người thật

---

## 📝 Định dạng bản ghi

Bản ghi được lưu dưới dạng JSON:

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

MIT License — Sử dụng tự do cho mục đích cá nhân và thương mại.
