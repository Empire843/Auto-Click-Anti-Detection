"""
GUI cho Auto-Click Tool sử dụng CustomTkinter.
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk
import keyboard

from models import MouseEvent, Recording, EventType
from recorder import MouseRecorder
from player import MousePlayer
from playlist import PlaylistController
from humanizer import HumanizeSettings
from utils import ensure_recordings_dir, format_duration, format_number, get_timestamp, get_recordings_dir, set_recordings_dir

# Theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Colors
BG_DARK = "#0f0f14"
BG_CARD = "#1a1a24"
BG_CARD_HOVER = "#22222e"
ACCENT = "#6c5ce7"
ACCENT_LIGHT = "#a29bfe"
RED = "#ff4757"
RED_DARK = "#c0392b"
GREEN = "#2ed573"
GREEN_DARK = "#27ae60"
YELLOW = "#ffa502"
TEXT = "#e8e8ef"
TEXT_DIM = "#8888a0"
BORDER = "#2a2a3a"


class AutoClickApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("⚡ Auto-Click Tool - Anti-Detection")
        self.geometry("1060x760")
        self.minsize(960, 680)
        self.configure(fg_color=BG_DARK)

        self.recorder = MouseRecorder()
        self.player = MousePlayer()
        self.playlist = PlaylistController()
        self.current_recording: Optional[Recording] = None
        self._timer_id = None
        self._canvas_points = []
        self._playlist_timer_id = None

        self.recorder.on_event_recorded = self._on_event_recorded
        self.player.on_playback_finished = self._on_playback_finished
        self.playlist.on_item_started = self._on_playlist_item_started
        self.playlist.on_playlist_finished = self._on_playlist_finished

        self._build_ui()
        self._setup_hotkeys()
        self._update_status("idle")
        ensure_recordings_dir()

    def _build_ui(self):
        # Top bar
        top = ctk.CTkFrame(self, fg_color=BG_CARD, height=56, corner_radius=0)
        top.pack(fill="x")
        top.pack_propagate(False)
        ctk.CTkLabel(top, text="⚡ AUTO-CLICK  ·  Anti-Detection", font=("Segoe UI", 18, "bold"),
                      text_color=ACCENT_LIGHT).pack(side="left", padx=16)
        self._status_label = ctk.CTkLabel(top, text="● SẴN SÀNG", font=("Segoe UI", 13),
                                           text_color=GREEN)
        self._status_label.pack(side="right", padx=16)

        # Main content
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=12, pady=8)

        # Left panel - controls
        left = ctk.CTkFrame(main, fg_color="transparent", width=280)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)
        self._build_controls(left)

        # Right panel - canvas + tabs
        right = ctk.CTkFrame(main, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)
        self._build_canvas(right)
        self._build_tabs(right)

        # Bottom bar
        self._build_bottom_bar()

    def _build_controls(self, parent):
        # Record section
        sec1 = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        sec1.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(sec1, text="🎬 GHI LẠI", font=("Segoe UI", 14, "bold"),
                      text_color=TEXT).pack(anchor="w", padx=14, pady=(12, 6))

        self._btn_record = ctk.CTkButton(
            sec1, text="⏺  Bắt đầu ghi  (F6)", font=("Segoe UI", 13, "bold"),
            fg_color=RED, hover_color=RED_DARK, height=42, corner_radius=10,
            command=self._toggle_record
        )
        self._btn_record.pack(fill="x", padx=14, pady=(4, 12))

        self._record_time_label = ctk.CTkLabel(sec1, text="00.00s", font=("Consolas", 22, "bold"),
                                                text_color=TEXT)
        self._record_time_label.pack(pady=(0, 10))

        # Play section
        sec2 = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        sec2.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(sec2, text="▶ PHÁT LẠI", font=("Segoe UI", 14, "bold"),
                      text_color=TEXT).pack(anchor="w", padx=14, pady=(12, 6))

        self._btn_play = ctk.CTkButton(
            sec2, text="▶  Phát lại  (F7)", font=("Segoe UI", 13, "bold"),
            fg_color=GREEN_DARK, hover_color="#1e8449", height=42, corner_radius=10,
            command=self._toggle_play, state="disabled"
        )
        self._btn_play.pack(fill="x", padx=14, pady=(4, 8))

        # Speed
        speed_frame = ctk.CTkFrame(sec2, fg_color="transparent")
        speed_frame.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(speed_frame, text="Tốc độ:", font=("Segoe UI", 12),
                      text_color=TEXT_DIM).pack(side="left")
        self._speed_label = ctk.CTkLabel(speed_frame, text="1.0x", font=("Segoe UI", 12, "bold"),
                                          text_color=ACCENT_LIGHT)
        self._speed_label.pack(side="right")

        self._speed_slider = ctk.CTkSlider(
            sec2, from_=0.1, to=5.0, number_of_steps=49,
            command=self._on_speed_change, button_color=ACCENT,
            button_hover_color=ACCENT_LIGHT, progress_color=ACCENT
        )
        self._speed_slider.set(1.0)
        self._speed_slider.pack(fill="x", padx=14, pady=(0, 8))

        # Loop count
        loop_frame = ctk.CTkFrame(sec2, fg_color="transparent")
        loop_frame.pack(fill="x", padx=14, pady=(0, 4))
        ctk.CTkLabel(loop_frame, text="Lặp lại:", font=("Segoe UI", 12),
                      text_color=TEXT_DIM).pack(side="left")

        self._loop_var = ctk.StringVar(value="1")
        self._loop_entry = ctk.CTkEntry(
            loop_frame, width=60, font=("Segoe UI", 12), textvariable=self._loop_var,
            fg_color=BG_DARK, border_color=BORDER, justify="center"
        )
        self._loop_entry.pack(side="right")
        ctk.CTkLabel(loop_frame, text="(0 = vô hạn)", font=("Segoe UI", 10),
                      text_color=TEXT_DIM).pack(side="right", padx=6)

        # Interval (khoảng cách giữa các lần lặp)
        interval_frame = ctk.CTkFrame(sec2, fg_color="transparent")
        interval_frame.pack(fill="x", padx=14, pady=(0, 4))
        ctk.CTkLabel(interval_frame, text="Nghỉ giữa lần lặp:", font=("Segoe UI", 12),
                      text_color=TEXT_DIM).pack(side="left")

        self._interval_var = ctk.StringVar(value="0")
        self._interval_entry = ctk.CTkEntry(
            interval_frame, width=60, font=("Segoe UI", 12), textvariable=self._interval_var,
            fg_color=BG_DARK, border_color=BORDER, justify="center"
        )
        self._interval_entry.pack(side="right")
        ctk.CTkLabel(interval_frame, text="giây", font=("Segoe UI", 10),
                      text_color=TEXT_DIM).pack(side="right", padx=6)

        # Interval status label
        self._interval_status = ctk.CTkLabel(sec2, text="", font=("Segoe UI", 11),
                                              text_color=YELLOW)
        self._interval_status.pack(padx=14, pady=(0, 2))

        # Progress
        self._progress = ctk.CTkProgressBar(sec2, progress_color=GREEN, fg_color=BG_DARK, height=6)
        self._progress.set(0)
        self._progress.pack(fill="x", padx=14, pady=(4, 12))

        # Emergency stop
        self._btn_stop = ctk.CTkButton(
            parent, text="⛔  DỪNG KHẨN CẤP  (F8)", font=("Segoe UI", 13, "bold"),
            fg_color="#2c2c3a", hover_color=RED, height=38, corner_radius=10,
            border_width=1, border_color=RED, text_color=RED,
            command=self._emergency_stop
        )
        self._btn_stop.pack(fill="x", pady=(0, 8))

        # Anti-Detection settings
        sec_anti = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        sec_anti.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(sec_anti, text="🛡 ANTI-DETECTION", font=("Segoe UI", 14, "bold"),
                      text_color=TEXT).pack(anchor="w", padx=14, pady=(12, 6))

        # Humanize toggle
        self._humanize_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            sec_anti, text="Humanize chuyển động", font=("Segoe UI", 12),
            variable=self._humanize_var, command=self._on_humanize_toggle,
            progress_color=GREEN, button_color=ACCENT, text_color=TEXT_DIM
        ).pack(anchor="w", padx=14, pady=2)

        # Win32 SendInput toggle
        self._win32_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            sec_anti, text="Win32 SendInput (HW)", font=("Segoe UI", 12),
            variable=self._win32_var, command=self._on_humanize_toggle,
            progress_color=GREEN, button_color=ACCENT, text_color=TEXT_DIM
        ).pack(anchor="w", padx=14, pady=2)

        # Bezier curves toggle
        self._bezier_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            sec_anti, text="Bezier curves", font=("Segoe UI", 12),
            variable=self._bezier_var, command=self._on_humanize_toggle,
            progress_color=GREEN, button_color=ACCENT, text_color=TEXT_DIM
        ).pack(anchor="w", padx=14, pady=2)

        # Micro-tremor toggle
        self._tremor_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            sec_anti, text="Micro-tremor (rung tay)", font=("Segoe UI", 12),
            variable=self._tremor_var, command=self._on_humanize_toggle,
            progress_color=GREEN, button_color=ACCENT, text_color=TEXT_DIM
        ).pack(anchor="w", padx=14, pady=(2, 10))

        # File operations
        sec3 = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        sec3.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(sec3, text="💾 FILE", font=("Segoe UI", 14, "bold"),
                      text_color=TEXT).pack(anchor="w", padx=14, pady=(12, 6))

        btn_frame = ctk.CTkFrame(sec3, fg_color="transparent")
        btn_frame.pack(fill="x", padx=14, pady=(0, 6))

        ctk.CTkButton(
            btn_frame, text="💾 Lưu", font=("Segoe UI", 12), width=80,
            fg_color=ACCENT, hover_color=ACCENT_LIGHT, height=34, corner_radius=8,
            command=self._save_recording
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        ctk.CTkButton(
            btn_frame, text="📂 Mở", font=("Segoe UI", 12), width=80,
            fg_color="#2c2c3a", hover_color=BG_CARD_HOVER, height=34, corner_radius=8,
            border_width=1, border_color=BORDER,
            command=self._load_recording
        ).pack(side="left", expand=True, fill="x", padx=(4, 0))

        # Folder selection
        folder_frame = ctk.CTkFrame(sec3, fg_color="transparent")
        folder_frame.pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkButton(
            folder_frame, text="📁", font=("Segoe UI", 12), width=32,
            fg_color="#2c2c3a", hover_color=BG_CARD_HOVER, height=26, corner_radius=6,
            command=self._select_recordings_folder
        ).pack(side="left", padx=(0, 6))

        rec_dir = get_recordings_dir()
        short = rec_dir if len(rec_dir) <= 25 else "..." + rec_dir[-22:]
        self._folder_label = ctk.CTkLabel(
            folder_frame, text=short, font=("Segoe UI", 10),
            text_color=TEXT_DIM
        )
        self._folder_label.pack(side="left", fill="x")

    def _build_canvas(self, parent):
        canvas_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        canvas_frame.pack(fill="both", expand=True, pady=(0, 8))

        header = ctk.CTkFrame(canvas_frame, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(header, text="🖱 QUỸ ĐẠO CHUỘT", font=("Segoe UI", 13, "bold"),
                      text_color=TEXT).pack(side="left")
        self._btn_clear = ctk.CTkButton(
            header, text="🗑 Xóa", font=("Segoe UI", 11), width=60,
            fg_color="transparent", hover_color=BG_CARD_HOVER, height=28,
            text_color=TEXT_DIM, command=self._clear_canvas
        )
        self._btn_clear.pack(side="right")

        self._canvas = tk.Canvas(
            canvas_frame, bg="#12121a", highlightthickness=1,
            highlightbackground=BORDER, cursor="crosshair"
        )
        self._canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _build_tabs(self, parent):
        """Tạo tabview với Events và Playlist."""
        self._tabview = ctk.CTkTabview(parent, fg_color=BG_CARD, corner_radius=12,
                                        segmented_button_fg_color=BG_DARK,
                                        segmented_button_selected_color=ACCENT,
                                        segmented_button_unselected_color="#2c2c3a",
                                        height=240)
        self._tabview.pack(fill="both", expand=False, pady=(0, 0))

        tab_events = self._tabview.add("📋 Sự kiện")
        tab_playlist = self._tabview.add("📁 Playlist")

        self._build_event_list(tab_events)
        self._build_playlist_panel(tab_playlist)

    def _build_event_list(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(6, 2))
        self._event_count_label = ctk.CTkLabel(header, text="0 events", font=("Segoe UI", 11),
                                                text_color=TEXT_DIM)
        self._event_count_label.pack(side="right")

        self._event_text = ctk.CTkTextbox(
            parent, font=("Consolas", 11), fg_color="#0d0d12",
            text_color=TEXT_DIM, corner_radius=8, wrap="none"
        )
        self._event_text.pack(fill="both", expand=True, padx=8, pady=(0, 6))

    def _build_playlist_panel(self, parent):
        """Panel quản lý playlist."""
        # Top controls
        ctrl = ctk.CTkFrame(parent, fg_color="transparent")
        ctrl.pack(fill="x", padx=8, pady=(6, 4))

        ctk.CTkButton(
            ctrl, text="➕ Thêm", font=("Segoe UI", 11), width=70,
            fg_color=ACCENT, hover_color=ACCENT_LIGHT, height=30, corner_radius=8,
            command=self._playlist_add
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            ctrl, text="🗑 Xóa", font=("Segoe UI", 11), width=60,
            fg_color="#2c2c3a", hover_color=RED, height=30, corner_radius=8,
            border_width=1, border_color=BORDER,
            command=self._playlist_remove
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            ctrl, text="⬆", font=("Segoe UI", 11), width=32,
            fg_color="#2c2c3a", hover_color=BG_CARD_HOVER, height=30, corner_radius=8,
            command=self._playlist_move_up
        ).pack(side="left", padx=(0, 2))

        ctk.CTkButton(
            ctrl, text="⬇", font=("Segoe UI", 11), width=32,
            fg_color="#2c2c3a", hover_color=BG_CARD_HOVER, height=30, corner_radius=8,
            command=self._playlist_move_down
        ).pack(side="left", padx=(0, 4))

        self._pl_count_label = ctk.CTkLabel(ctrl, text="0 bản ghi", font=("Segoe UI", 11),
                                             text_color=TEXT_DIM)
        self._pl_count_label.pack(side="right")

        # Playlist listbox
        self._pl_listbox = tk.Listbox(
            parent, bg="#0d0d12", fg=TEXT_DIM, font=("Consolas", 11),
            selectbackground=ACCENT, selectforeground="white",
            highlightthickness=1, highlightcolor=BORDER, highlightbackground=BORDER,
            borderwidth=0, activestyle="none"
        )
        self._pl_listbox.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        # Bottom: Run All controls
        bottom = ctk.CTkFrame(parent, fg_color="transparent")
        bottom.pack(fill="x", padx=8, pady=(0, 6))

        # Cycles + interval
        settings_row = ctk.CTkFrame(bottom, fg_color="transparent")
        settings_row.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(settings_row, text="Lặp:", font=("Segoe UI", 11),
                      text_color=TEXT_DIM).pack(side="left")
        self._pl_cycles_var = ctk.StringVar(value="1")
        ctk.CTkEntry(
            settings_row, width=45, font=("Segoe UI", 11), textvariable=self._pl_cycles_var,
            fg_color=BG_DARK, border_color=BORDER, justify="center"
        ).pack(side="left", padx=(4, 8))

        ctk.CTkLabel(settings_row, text="Nghỉ:", font=("Segoe UI", 11),
                      text_color=TEXT_DIM).pack(side="left")
        self._pl_interval_var = ctk.StringVar(value="2")
        ctk.CTkEntry(
            settings_row, width=45, font=("Segoe UI", 11), textvariable=self._pl_interval_var,
            fg_color=BG_DARK, border_color=BORDER, justify="center"
        ).pack(side="left", padx=(4, 2))
        ctk.CTkLabel(settings_row, text="giây", font=("Segoe UI", 10),
                      text_color=TEXT_DIM).pack(side="left")

        # Playlist status
        self._pl_status_label = ctk.CTkLabel(settings_row, text="", font=("Segoe UI", 11),
                                              text_color=YELLOW)
        self._pl_status_label.pack(side="right")

        # Run All button
        self._btn_run_all = ctk.CTkButton(
            bottom, text="🚀  RUN ALL", font=("Segoe UI", 13, "bold"),
            fg_color="#e17055", hover_color="#d63031", height=38, corner_radius=10,
            command=self._toggle_run_all
        )
        self._btn_run_all.pack(fill="x")

    def _build_bottom_bar(self):
        bottom = ctk.CTkFrame(self, fg_color=BG_CARD, height=36, corner_radius=0)
        bottom.pack(fill="x", side="bottom")
        bottom.pack_propagate(False)

        self._stats_label = ctk.CTkLabel(
            bottom, text="Events: 0  |  Clicks: 0  |  Duration: 0s",
            font=("Segoe UI", 11), text_color=TEXT_DIM
        )
        self._stats_label.pack(side="left", padx=14)

        ctk.CTkLabel(
            bottom, text="F6: Record  |  F7: Play  |  F8: Stop",
            font=("Segoe UI", 11), text_color=TEXT_DIM
        ).pack(side="right", padx=14)

    # === Hotkeys ===
    def _setup_hotkeys(self):
        keyboard.add_hotkey('F6', self._toggle_record_safe)
        keyboard.add_hotkey('F7', self._toggle_play_safe)
        keyboard.add_hotkey('F8', self._emergency_stop_safe)

    def _toggle_record_safe(self):
        self.after(0, self._toggle_record)

    def _toggle_play_safe(self):
        self.after(0, self._toggle_play)

    def _emergency_stop_safe(self):
        self.after(0, self._emergency_stop)

    # === Record ===
    def _toggle_record(self):
        if self.recorder.is_recording:
            self._stop_record()
        else:
            self._start_record()

    def _start_record(self):
        if self.player.is_playing:
            self._emergency_stop()

        self._clear_canvas()
        self._event_text.delete("1.0", "end")
        self._canvas_points = []

        self.recorder.start()
        self._update_status("recording")
        self._btn_record.configure(text="⏹  Dừng ghi  (F6)", fg_color="#c0392b")
        self._btn_play.configure(state="disabled")
        self._start_timer()

    def _stop_record(self):
        recording = self.recorder.stop()
        if recording:
            self.current_recording = recording
            self._btn_play.configure(state="normal")
            self._draw_full_trajectory()

        self._update_status("idle")
        self._btn_record.configure(text="⏺  Bắt đầu ghi  (F6)", fg_color=RED)
        self._stop_timer()
        self._update_stats()

    # === Play ===
    def _toggle_play(self):
        if self.player.is_playing:
            self.player.stop()
            self._update_status("idle")
            self._btn_play.configure(text="▶  Phát lại  (F7)", fg_color=GREEN_DARK)
            self._stop_play_timer()
        else:
            self._start_play()

    def _start_play(self):
        if not self.current_recording or not self.current_recording.events:
            return
        if self.recorder.is_recording:
            self._stop_record()

        try:
            loop_count = int(self._loop_var.get())
        except ValueError:
            loop_count = 1

        try:
            interval = float(self._interval_var.get())
        except ValueError:
            interval = 0.0

        # Apply anti-detection settings
        self._apply_humanize_settings()

        self.player.speed = self._speed_slider.get()
        self.player.loop_count = loop_count
        self.player.loop_interval = interval
        self.player.start(self.current_recording)

        self._update_status("playing")
        self._btn_play.configure(text="⏹  Dừng phát  (F7)", fg_color="#c0392b")
        self._btn_record.configure(state="disabled")
        self._start_play_timer()

    def _on_playback_finished(self):
        self.after(0, self._playback_done)

    def _playback_done(self):
        self._update_status("idle")
        self._btn_play.configure(text="▶  Phát lại  (F7)", fg_color=GREEN_DARK)
        self._btn_record.configure(state="normal")
        self._progress.set(0)
        self._interval_status.configure(text="")
        self._stop_play_timer()

    # === Emergency Stop ===
    def _emergency_stop(self):
        if self.recorder.is_recording:
            self.recorder.stop()
            self._btn_record.configure(text="⏺  Bắt đầu ghi  (F6)", fg_color=RED)

        if self.player.is_playing:
            self.player.stop()
            self._btn_play.configure(text="▶  Phát lại  (F7)", fg_color=GREEN_DARK)

        if self.playlist.is_running:
            self.playlist.stop()
            self._btn_run_all.configure(text="🚀  RUN ALL", fg_color="#e17055")
            self._pl_status_label.configure(text="")
            self._stop_playlist_timer()

        self._btn_record.configure(state="normal")
        self._btn_play.configure(state="normal" if self.current_recording else "disabled")
        self._update_status("idle")
        self._stop_timer()
        self._stop_play_timer()

    # === File I/O ===
    def _select_recordings_folder(self):
        """Chọn thư mục lưu recordings."""
        current = get_recordings_dir()
        folder = filedialog.askdirectory(initialdir=current, title="Chọn thư mục lưu bản ghi")
        if folder:
            set_recordings_dir(folder)
            os.makedirs(folder, exist_ok=True)
            short = folder if len(folder) <= 25 else "..." + folder[-22:]
            self._folder_label.configure(text=short)

    def _save_recording(self):
        if not self.current_recording or not self.current_recording.events:
            messagebox.showwarning("Thông báo", "Chưa có recording nào để lưu!")
            return

        filepath = filedialog.asksaveasfilename(
            initialdir=get_recordings_dir(),
            initialfile=f"recording_{get_timestamp()}.json",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")]
        )
        if filepath:
            self.current_recording.save_to_file(filepath)
            self._update_status("idle")

    def _load_recording(self):
        filepath = filedialog.askopenfilename(
            initialdir=get_recordings_dir(),
            filetypes=[("JSON Files", "*.json")]
        )
        if filepath:
            try:
                self.current_recording = Recording.load_from_file(filepath)
                self._btn_play.configure(state="normal")
                self._draw_full_trajectory()
                self._update_stats()
                self._update_event_list_full()
                self._update_status("idle")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tải file:\n{e}")

    # === Canvas Drawing ===
    def _draw_full_trajectory(self):
        if not self.current_recording:
            return

        self._canvas.delete("all")
        cw = self._canvas.winfo_width() or 400
        ch = self._canvas.winfo_height() or 300
        sw = self.current_recording.screen_width or 1920
        sh = self.current_recording.screen_height or 1080

        scale_x = cw / sw
        scale_y = ch / sh

        points = []
        for e in self.current_recording.events:
            cx = int(e.x * scale_x)
            cy = int(e.y * scale_y)

            if e.event_type == EventType.MOVE:
                points.append((cx, cy))
            elif e.event_type == EventType.CLICK and e.pressed:
                # Draw click marker
                color = "#ff4757" if e.button == "left" else "#ffa502"
                self._canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5,
                                          fill=color, outline="white", width=1)

        # Draw trajectory line
        if len(points) >= 2:
            for i in range(1, len(points)):
                # Gradient color from accent to accent_light
                ratio = i / len(points)
                r = int(108 + (162 - 108) * ratio)
                g = int(92 + (155 - 92) * ratio)
                b = int(231 + (254 - 231) * ratio)
                color = f"#{r:02x}{g:02x}{b:02x}"

                self._canvas.create_line(
                    points[i - 1][0], points[i - 1][1],
                    points[i][0], points[i][1],
                    fill=color, width=1.5, smooth=True
                )

    def _clear_canvas(self):
        self._canvas.delete("all")
        self._canvas_points = []

    # === Event Recording Callback ===
    def _on_event_recorded(self, event: MouseEvent):
        self.after(0, lambda: self._append_event_display(event))

    def _append_event_display(self, event: MouseEvent):
        if event.event_type == EventType.MOVE:
            return  # Don't spam move events in the list

        icon = {"click": "🖱", "scroll": "📜"}.get(event.event_type, "➡")
        if event.event_type == EventType.CLICK:
            action = "Press" if event.pressed else "Release"
            text = f"{icon} [{event.timestamp:8.3f}s] Click {event.button} {action} @ ({event.x}, {event.y})\n"
        elif event.event_type == EventType.SCROLL:
            text = f"{icon} [{event.timestamp:8.3f}s] Scroll dy={event.scroll_dy} @ ({event.x}, {event.y})\n"
        else:
            return

        self._event_text.insert("end", text)
        self._event_text.see("end")

    def _update_event_list_full(self):
        self._event_text.delete("1.0", "end")
        if not self.current_recording:
            return

        count = 0
        for event in self.current_recording.events:
            if event.event_type == EventType.MOVE:
                continue
            count += 1
            if count > 500:
                self._event_text.insert("end", f"... và {self.current_recording.total_events - 500} events nữa\n")
                break
            self._append_event_display(event)

    # === Timer ===
    def _start_timer(self):
        self._update_record_time()

    def _update_record_time(self):
        if self.recorder.is_recording:
            elapsed = self.recorder.elapsed_time
            self._record_time_label.configure(text=format_duration(elapsed))
            self._timer_id = self.after(50, self._update_record_time)

    def _stop_timer(self):
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None

    _play_timer_id = None

    def _start_play_timer(self):
        self._update_play_progress()

    def _update_play_progress(self):
        if self.player.is_playing:
            self._progress.set(self.player.progress)
            # Hiển thị trạng thái chờ interval
            if self.player.is_waiting_interval:
                loop = self.player.current_loop
                total = self.player.loop_count
                total_str = str(total) if total > 0 else "∞"
                self._interval_status.configure(
                    text=f"⏳ Đang nghỉ... (lần {loop}/{total_str})"
                )
            else:
                loop = self.player.current_loop
                total = self.player.loop_count
                total_str = str(total) if total > 0 else "∞"
                self._interval_status.configure(
                    text=f"▶ Đang phát lần {loop}/{total_str}"
                )
            self._play_timer_id = self.after(50, self._update_play_progress)

    def _stop_play_timer(self):
        if self._play_timer_id:
            self.after_cancel(self._play_timer_id)
            self._play_timer_id = None

    # === Status ===
    def _update_status(self, status: str):
        config = {
            "idle": ("● SẴN SÀNG", GREEN),
            "recording": ("⏺ ĐANG GHI...", RED),
            "playing": ("▶ ĐANG PHÁT...", YELLOW),
            "playlist": ("🚀 PLAYLIST...", "#e17055"),
        }
        text, color = config.get(status, ("● SẴN SÀNG", GREEN))
        self._status_label.configure(text=text, text_color=color)

    def _update_stats(self):
        if self.current_recording:
            r = self.current_recording
            self._stats_label.configure(
                text=f"Events: {format_number(r.total_events)}  |  "
                     f"Clicks: {format_number(r.total_clicks)}  |  "
                     f"Duration: {format_duration(r.duration)}"
            )
            self._event_count_label.configure(text=f"{format_number(r.total_events)} events")
            self._record_time_label.configure(text=format_duration(r.duration))

    # === Speed ===
    def _on_speed_change(self, value):
        self._speed_label.configure(text=f"{value:.1f}x")
        self.player.speed = value

    # === Anti-Detection Settings ===
    def _on_humanize_toggle(self):
        self._apply_humanize_settings()

    def _apply_humanize_settings(self):
        humanize_on = self._humanize_var.get()
        settings = HumanizeSettings(
            enabled=humanize_on,
            use_win32=self._win32_var.get(),
            bezier_curvature=0.25 if self._bezier_var.get() else 0.0,
            micro_tremor=self._tremor_var.get(),
            position_noise=1.0 if humanize_on else 0.0,
            timing_noise=1.0 if humanize_on else 0.0,
        )
        self.player.humanize_settings = settings

    # === Playlist Methods ===
    def _playlist_add(self):
        """Thêm recordings vào playlist."""
        filepaths = filedialog.askopenfilenames(
            initialdir=get_recordings_dir(),
            filetypes=[("JSON Files", "*.json")]
        )
        for fp in filepaths:
            try:
                rec = Recording.load_from_file(fp)
                self.playlist.add_item(fp, rec)
            except Exception as e:
                print(f"Lỗi tải {fp}: {e}")
        self._refresh_playlist()

    def _playlist_remove(self):
        sel = self._pl_listbox.curselection()
        if sel:
            self.playlist.remove_item(sel[0])
            self._refresh_playlist()

    def _playlist_move_up(self):
        sel = self._pl_listbox.curselection()
        if sel and sel[0] > 0:
            idx = sel[0]
            self.playlist.move_up(idx)
            self._refresh_playlist()
            self._pl_listbox.selection_set(idx - 1)

    def _playlist_move_down(self):
        sel = self._pl_listbox.curselection()
        if sel and sel[0] < len(self.playlist.items) - 1:
            idx = sel[0]
            self.playlist.move_down(idx)
            self._refresh_playlist()
            self._pl_listbox.selection_set(idx + 1)

    def _refresh_playlist(self):
        """Cập nhật hiển thị playlist."""
        self._pl_listbox.delete(0, tk.END)
        for i, item in enumerate(self.playlist.items):
            dur = format_duration(item.duration)
            clicks = item.click_count
            name = item.name
            if len(name) > 30:
                name = name[:27] + "..."
            self._pl_listbox.insert(tk.END, f" {i+1}. {name}  ({dur}, {clicks} clicks)")
        self._pl_count_label.configure(text=f"{len(self.playlist.items)} bản ghi")

    def _toggle_run_all(self):
        if self.playlist.is_running:
            self.playlist.stop()
            self._btn_run_all.configure(text="🚀  RUN ALL", fg_color="#e17055")
            self._update_status("idle")
            self._pl_status_label.configure(text="")
            self._stop_playlist_timer()
        else:
            self._start_run_all()

    def _start_run_all(self):
        if not self.playlist.items:
            messagebox.showwarning("Thông báo", "Playlist trống! Hãy thêm bản ghi trước.")
            return

        # Dừng các hoạt động khác
        if self.recorder.is_recording:
            self._stop_record()
        if self.player.is_playing:
            self.player.stop()

        try:
            cycles = int(self._pl_cycles_var.get())
        except ValueError:
            cycles = 1
        try:
            interval = float(self._pl_interval_var.get())
        except ValueError:
            interval = 2.0

        self._apply_humanize_settings()

        self.playlist.start(
            speed=self._speed_slider.get(),
            total_cycles=cycles,
            interval=interval,
            humanize_settings=self.player.humanize_settings
        )

        self._btn_run_all.configure(text="⏹  DẮng playlist", fg_color="#c0392b")
        self._btn_record.configure(state="disabled")
        self._btn_play.configure(state="disabled")
        self._update_status("playlist")
        self._start_playlist_timer()

    def _on_playlist_item_started(self, idx, item):
        self.after(0, lambda: self._highlight_playlist_item(idx))

    def _highlight_playlist_item(self, idx):
        self._pl_listbox.selection_clear(0, tk.END)
        self._pl_listbox.selection_set(idx)
        self._pl_listbox.see(idx)

    def _on_playlist_finished(self):
        self.after(0, self._playlist_done)

    def _playlist_done(self):
        self._btn_run_all.configure(text="🚀  RUN ALL", fg_color="#e17055")
        self._btn_record.configure(state="normal")
        self._btn_play.configure(state="normal" if self.current_recording else "disabled")
        self._update_status("idle")
        self._pl_status_label.configure(text="✅ Hoàn thành!")
        self._stop_playlist_timer()

    def _start_playlist_timer(self):
        self._update_playlist_status()

    def _update_playlist_status(self):
        if self.playlist.is_running:
            idx = self.playlist.current_index + 1
            total = self.playlist.item_count
            cycle = self.playlist.current_cycle
            total_cycles = self.playlist.total_cycles
            cycle_str = str(total_cycles) if total_cycles > 0 else "∞"

            if self.playlist.is_waiting:
                self._pl_status_label.configure(text=f"⏳ Nghỉ... ({cycle}/{cycle_str})")
            else:
                self._pl_status_label.configure(text=f"▶ {idx}/{total} (vòng {cycle}/{cycle_str})")

            self._playlist_timer_id = self.after(100, self._update_playlist_status)

    def _stop_playlist_timer(self):
        if self._playlist_timer_id:
            self.after_cancel(self._playlist_timer_id)
            self._playlist_timer_id = None

    def destroy(self):
        keyboard.unhook_all()
        if self.recorder.is_recording:
            self.recorder.stop()
        if self.player.is_playing:
            self.player.stop()
        if self.playlist.is_running:
            self.playlist.stop()
        super().destroy()
