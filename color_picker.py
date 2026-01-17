from __future__ import annotations

import colorsys
import json
import re
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

import ttkbootstrap as tb


class ColorPickerApp:
    """Enhanced color picker helper with history, copying, and live preview."""

    HISTORY_LIMIT = 10
    FAVORITES_FILE = Path.home() / ".color_picker_favorites.json"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("🎨 Color Picker")
        self.root.geometry("640x760")
        self.root.minsize(360, 320)
        self.root.resizable(True, True)

        self._status_after_id: str | None = None
        self.current_color = {"hex": "#3498DB", "rgb": (52, 152, 219)}
        self.history: list[str] = []
        self.favorites: list[str] = []
        self.custom_background = "#1F2937"
        self._updating_sliders = False

        self.hue_var = tk.IntVar(value=210)
        self.sat_var = tk.IntVar(value=76)
        self.val_var = tk.IntVar(value=86)

        self._build_ui()
        self._load_favorites()
        self.set_color(self.current_color["hex"], add_to_history=False)
        self._set_status("Pick a color to get started.")

    def _build_ui(self) -> None:
        style = tb.Style(theme="flatly")
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 11))
        style.configure("TLabelframe.Label", font=("Segoe UI", 11, "bold"))

        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(container, highlightthickness=0)
        v_scroll = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=v_scroll.set)

        self.main_frame = ttk.Frame(self.canvas, padding=(20, 18))
        self._canvas_window = self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")

        self.main_frame.bind(
            "<Configure>", lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all") or (0, 0, 0, 0))
        )
        self.canvas.bind("<Configure>", self._resize_canvas_window)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        self.root.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.root.bind_all("<Button-4>", self._on_linux_scroll, add="+")
        self.root.bind_all("<Button-5>", self._on_linux_scroll, add="+")

        self.main_frame.columnconfigure(0, weight=1)

        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.columnconfigure(0, weight=1)

        ttk.Label(header_frame, text="Color Palette Studio", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        header_actions = ttk.Frame(header_frame)
        header_actions.grid(row=0, column=1, sticky="e")
        ttk.Button(header_actions, text="Export JSON", command=self.export_palette).pack(side="left", padx=(0, 8))
        ttk.Button(header_actions, text="Import JSON", command=self.import_palette).pack(side="left")

        preview_frame = ttk.LabelFrame(self.main_frame, text="Preview", padding=15)
        preview_frame.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        preview_frame.columnconfigure(0, weight=1)

        self.preview = tk.Canvas(preview_frame, width=200, height=110, highlightthickness=0, bd=0)
        self.preview_rect = self.preview.create_rectangle(
            2, 2, 198, 108, outline="#d1d5db", width=1, fill=self.current_color["hex"]
        )
        self.preview.pack()

        info_frame = ttk.LabelFrame(self.main_frame, text="Color values", padding=15)
        info_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        info_frame.columnconfigure(0, weight=1)

        self.hex_display = tk.StringVar(value="HEX: #------")
        self.rgb_display = tk.StringVar(value="RGB: (---, ---, ---)")
        self.hsl_display = tk.StringVar(value="HSL: (---°, ---, ---)")
        self.hsv_display = tk.StringVar(value="HSV: (---°, ---, ---)")

        ttk.Label(info_frame, textvariable=self.hex_display, font=("Consolas", 13)).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Label(info_frame, textvariable=self.rgb_display, font=("Consolas", 13)).grid(
            row=1, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Label(info_frame, textvariable=self.hsl_display, font=("Consolas", 13)).grid(
            row=2, column=0, sticky="w"
        )
        ttk.Label(info_frame, textvariable=self.hsv_display, font=("Consolas", 13)).grid(
            row=3, column=0, sticky="w"
        )

        copy_row = ttk.Frame(info_frame)
        copy_row.grid(row=0, column=1, rowspan=4, sticky="e")
        ttk.Button(
            copy_row, text="Copy HEX", command=lambda: self.copy_to_clipboard(self.current_color["hex"], "HEX")
        ).pack(fill="x", pady=(0, 6))
        ttk.Button(
            copy_row,
            text="Copy RGB",
            command=lambda: self.copy_to_clipboard(self._format_rgb(self.current_color["rgb"]), "RGB"),
        ).pack(fill="x", pady=(0, 6))
        ttk.Button(
            copy_row,
            text="Copy HSL",
            command=lambda: self.copy_to_clipboard(self._format_hsl(self.current_color["rgb"]), "HSL"),
        ).pack(fill="x")

        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        control_frame.columnconfigure((0, 1, 2), weight=1)

        ttk.Button(control_frame, text="Pick a Color", command=self.pick_color).grid(
            row=0, column=0, padx=(0, 8), sticky="ew"
        )
        ttk.Button(control_frame, text="Add to Favorites", command=self.add_to_favorites).grid(
            row=0, column=1, padx=4, sticky="ew"
        )
        ttk.Button(control_frame, text="Copy HEX", command=lambda: self.copy_to_clipboard(self.current_color["hex"], "HEX")).grid(
            row=0, column=2, padx=(8, 0), sticky="ew"
        )

        slider_frame = ttk.LabelFrame(self.main_frame, text="HSV sliders", padding=15)
        slider_frame.grid(row=4, column=0, sticky="ew", pady=(16, 0))
        slider_frame.columnconfigure(1, weight=1)

        ttk.Label(slider_frame, text="Hue (°)").grid(row=0, column=0, sticky="w")
        hue_scale = ttk.Scale(
            slider_frame, from_=0, to=360, orient="horizontal", variable=self.hue_var, command=self._on_hsv_change
        )
        hue_scale.grid(row=0, column=1, sticky="ew", padx=(12, 0))
        ttk.Label(slider_frame, textvariable=self.hue_var, width=4).grid(row=0, column=2, padx=(8, 0))

        ttk.Label(slider_frame, text="Saturation (%)").grid(row=1, column=0, sticky="w", pady=(10, 0))
        sat_scale = ttk.Scale(
            slider_frame, from_=0, to=100, orient="horizontal", variable=self.sat_var, command=self._on_hsv_change
        )
        sat_scale.grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=(10, 0))
        ttk.Label(slider_frame, textvariable=self.sat_var, width=4).grid(row=1, column=2, padx=(8, 0), pady=(10, 0))

        ttk.Label(slider_frame, text="Value (%)").grid(row=2, column=0, sticky="w", pady=(10, 0))
        val_scale = ttk.Scale(
            slider_frame, from_=0, to=100, orient="horizontal", variable=self.val_var, command=self._on_hsv_change
        )
        val_scale.grid(row=2, column=1, sticky="ew", padx=(12, 0), pady=(10, 0))
        ttk.Label(slider_frame, textvariable=self.val_var, width=4).grid(row=2, column=2, padx=(8, 0), pady=(10, 0))

        for scale in (hue_scale, sat_scale, val_scale):
            scale.bind("<ButtonRelease-1>", self._commit_slider_color)

        manual_frame = ttk.LabelFrame(self.main_frame, text="Manual HEX input", padding=15)
        manual_frame.grid(row=5, column=0, sticky="ew", pady=(16, 0))
        manual_frame.columnconfigure(1, weight=1)

        ttk.Label(manual_frame, text="Enter HEX (#RGB/RRGGBB):").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.hex_entry_var = tk.StringVar()
        self.hex_entry = ttk.Entry(manual_frame, textvariable=self.hex_entry_var, font=("Consolas", 12), width=14)
        self.hex_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        ttk.Button(manual_frame, text="Apply", command=self.apply_hex_input).grid(row=0, column=2)

        contrast_frame = ttk.LabelFrame(self.main_frame, text="Contrast checks", padding=15)
        contrast_frame.grid(row=6, column=0, sticky="ew", pady=(16, 0))
        contrast_frame.columnconfigure(1, weight=1)

        self.contrast_white_var = tk.StringVar(value="White: --")
        self.contrast_black_var = tk.StringVar(value="Black: --")
        self.contrast_custom_var = tk.StringVar(value="Custom: --")

        ttk.Label(contrast_frame, textvariable=self.contrast_white_var, font=("Segoe UI", 11)).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(contrast_frame, textvariable=self.contrast_black_var, font=("Segoe UI", 11)).grid(
            row=1, column=0, sticky="w", pady=(6, 0)
        )

        custom_row = ttk.Frame(contrast_frame)
        custom_row.grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Label(custom_row, textvariable=self.contrast_custom_var, font=("Segoe UI", 11)).pack(side="left")
        self.custom_bg_swatch = tk.Canvas(custom_row, width=24, height=18, highlightthickness=1, highlightbackground="#cbd5e1")
        self.custom_bg_swatch.pack(side="left", padx=(8, 6))
        self.custom_bg_swatch.create_rectangle(1, 1, 22, 16, fill=self.custom_background, outline="")
        ttk.Button(custom_row, text="Pick background", command=self.pick_custom_background).pack(side="left")

        history_frame = ttk.LabelFrame(self.main_frame, text="Recent colors (double-click to reuse)", padding=15)
        history_frame.grid(row=7, column=0, sticky="nsew", pady=(16, 0))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(1, weight=1)

        self.history_swatches = ttk.Frame(history_frame)
        self.history_swatches.grid(row=0, column=0, sticky="ew", columnspan=2, pady=(0, 10))

        self.history_list = tk.Listbox(history_frame, height=6, activestyle="none", font=("Consolas", 12))
        self.history_list.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_list.yview)
        scrollbar.grid(row=1, column=1, sticky="nsw", padx=(6, 0))
        self.history_list.configure(yscrollcommand=scrollbar.set)
        self.history_list.bind("<Double-Button-1>", self.on_history_select)

        favorites_frame = ttk.LabelFrame(self.main_frame, text="Favorite colors (double-click to reuse)", padding=15)
        favorites_frame.grid(row=8, column=0, sticky="nsew", pady=(16, 0))
        favorites_frame.columnconfigure(0, weight=1)
        favorites_frame.rowconfigure(2, weight=1)

        fav_buttons_frame = ttk.Frame(favorites_frame)
        fav_buttons_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8), columnspan=2)
        ttk.Button(fav_buttons_frame, text="Remove Selected", command=self.remove_favorite).pack(side="left")

        self.favorites_swatches = ttk.Frame(favorites_frame)
        self.favorites_swatches.grid(row=1, column=0, sticky="ew", columnspan=2, pady=(0, 10))

        self.favorites_list = tk.Listbox(favorites_frame, height=6, activestyle="none", font=("Consolas", 12))
        self.favorites_list.grid(row=2, column=0, sticky="nsew")
        fav_scrollbar = ttk.Scrollbar(favorites_frame, orient="vertical", command=self.favorites_list.yview)
        fav_scrollbar.grid(row=2, column=1, sticky="nsw", padx=(6, 0))
        self.favorites_list.configure(yscrollcommand=fav_scrollbar.set)
        self.favorites_list.bind("<Double-Button-1>", self.on_favorite_select)

        status_frame = ttk.Frame(self.main_frame, padding=(0, 8, 0, 0))
        status_frame.grid(row=9, column=0, sticky="ew")
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 10), foreground="#555555").grid(
            row=0, column=0, sticky="w"
        )

    def pick_color(self) -> None:
        try:
            color = colorchooser.askcolor(initialcolor=self.current_color["hex"], title="Pick a color")
            if color and color[1]:
                self.set_color(color[1].upper())
            else:
                self._set_status("Color selection canceled.", duration=2000)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to pick color: {e}")
            self._set_status("Error picking color.", duration=2000)

    def apply_hex_input(self) -> None:
        try:
            raw_value = self.hex_entry_var.get().strip()
            if not raw_value:
                messagebox.showinfo("No value", "Enter a HEX value to apply.")
                return

            normalized = raw_value.upper()
            if not normalized.startswith("#"):
                normalized = f"#{normalized}"

            if not re.fullmatch(r"#([0-9A-F]{3}|[0-9A-F]{6})", normalized):
                messagebox.showerror("Invalid HEX", "Please enter a valid HEX color (e.g., #1A2B3C or #ABC).")
                return

            if len(normalized) == 4:
                normalized = f"#{normalized[1]*2}{normalized[2]*2}{normalized[3]*2}"

            self.set_color(normalized)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply HEX color: {e}")
            self._set_status("Error applying color.", duration=2000)

    def set_color(self, hex_value: str, add_to_history: bool = True) -> None:
        try:
            rgb = self._hex_to_rgb(hex_value)
            self.current_color = {"hex": hex_value, "rgb": rgb}
            self.hex_entry_var.set(hex_value)

            self.preview.itemconfig(self.preview_rect, fill=hex_value)
            self.hex_display.set(f"HEX: {hex_value}")
            self.rgb_display.set(f"RGB: {self._format_rgb(rgb)}")
            self.hsl_display.set(f"HSL: {self._format_hsl(rgb)}")
            self.hsv_display.set(f"HSV: {self._format_hsv(rgb)}")
            self._sync_sliders_from_rgb(rgb)
            self._update_contrast()

            if add_to_history:
                self._update_history(hex_value)
            self._set_status(f"Current color set to {hex_value}.", duration=2200)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set color: {e}")
            self._set_status("Error setting color.", duration=2000)

    def _update_history(self, hex_value: str) -> None:
        if hex_value in self.history:
            self.history.remove(hex_value)
        self.history.insert(0, hex_value)
        self.history = self.history[: self.HISTORY_LIMIT]

        self.history_list.delete(0, tk.END)
        for color in self.history:
            self.history_list.insert(tk.END, color)
        self._render_swatches(self.history_swatches, self.history, self.set_color)

    def on_history_select(self, event) -> None:
        selection = self.history_list.curselection()
        if not selection:
            return
        hex_value = self.history_list.get(selection[0])
        self.set_color(hex_value)

    def copy_to_clipboard(self, value: str, label: str) -> None:
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(value)
            self._set_status(f"{label} copied to clipboard.", duration=2000)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
            self._set_status("Error copying to clipboard.", duration=2000)

    def _format_rgb(self, rgb: tuple[int, int, int]) -> str:
        return f"{rgb[0]}, {rgb[1]}, {rgb[2]}"

    def _format_hsl(self, rgb: tuple[int, int, int]) -> str:
        r, g, b = (channel / 255 for channel in rgb)
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return f"{int(round(h * 360))}°, {int(round(s * 100))}%, {int(round(l * 100))}%"

    def _hex_to_rgb(self, hex_value: str) -> tuple[int, int, int]:
        return (int(hex_value[1:3], 16), int(hex_value[3:5], 16), int(hex_value[5:7], 16))

    def _format_hsv(self, rgb: tuple[int, int, int]) -> str:
        r, g, b = (channel / 255 for channel in rgb)
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        return f"{int(round(h * 360))}°, {int(round(s * 100))}%, {int(round(v * 100))}%"

    def _set_status(self, message: str, duration: int | None = None) -> None:
        if self._status_after_id is not None:
            self.root.after_cancel(self._status_after_id)
            self._status_after_id = None
        self.status_var.set(message)
        if duration:
            self._status_after_id = self.root.after(duration, self._reset_status)

    def _reset_status(self) -> None:
        self._status_after_id = None
        self.status_var.set("Ready.")

    def add_to_favorites(self) -> None:
        """Add current color to favorites list."""
        hex_value = self.current_color["hex"]
        if hex_value in self.favorites:
            self._set_status(f"{hex_value} is already in favorites.", duration=2000)
            return
        
        self.favorites.append(hex_value)
        self.favorites_list.insert(tk.END, hex_value)
        self._render_swatches(self.favorites_swatches, self.favorites, self.set_color)
        self._save_favorites()
        self._set_status(f"{hex_value} added to favorites.", duration=2000)

    def remove_favorite(self) -> None:
        """Remove selected color from favorites list."""
        selection = self.favorites_list.curselection()
        if not selection:
            messagebox.showinfo("No selection", "Please select a favorite color to remove.")
            return
        
        index = selection[0]
        hex_value = self.favorites_list.get(index)
        self.favorites_list.delete(index)
        self.favorites.remove(hex_value)
        self._render_swatches(self.favorites_swatches, self.favorites, self.set_color)
        self._save_favorites()
        self._set_status(f"{hex_value} removed from favorites.", duration=2000)

    def on_favorite_select(self, event) -> None:
        """Handle double-click on favorite color."""
        selection = self.favorites_list.curselection()
        if not selection:
            return
        hex_value = self.favorites_list.get(selection[0])
        self.set_color(hex_value)

    def _save_favorites(self) -> None:
        """Save favorites to JSON file."""
        try:
            with open(self.FAVORITES_FILE, "w") as f:
                json.dump(self.favorites, f, indent=2)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save favorites: {e}")

    def _load_favorites(self) -> None:
        """Load favorites from JSON file."""
        try:
            if self.FAVORITES_FILE.exists():
                with open(self.FAVORITES_FILE, "r") as f:
                    self.favorites = json.load(f)
                    for color in self.favorites:
                        self.favorites_list.insert(tk.END, color)
                self._render_swatches(self.favorites_swatches, self.favorites, self.set_color)
                self._set_status(f"Loaded {len(self.favorites)} favorite colors.", duration=2000)
        except Exception as e:
            messagebox.showwarning("Load Error", f"Failed to load favorites: {e}")
            self.favorites = []
            self._render_swatches(self.favorites_swatches, self.favorites, self.set_color)

    def _resize_canvas_window(self, event) -> None:
        self.canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event) -> None:
        delta = int(-1 * (event.delta / 120))
        if delta:
            self._scroll_canvas(delta)

    def _on_linux_scroll(self, event) -> None:
        if event.num == 4:
            self._scroll_canvas(-1)
        elif event.num == 5:
            self._scroll_canvas(1)

    def _scroll_canvas(self, units: int) -> None:
        bbox = self.canvas.bbox("all")
        if not bbox:
            return
        content_height = bbox[3] - bbox[1]
        if self.canvas.winfo_height() >= content_height:
            return
        self.canvas.yview_scroll(units, "units")

    def _render_swatches(self, parent: ttk.Frame, colors: list[str], command) -> None:
        for child in parent.winfo_children():
            child.destroy()

        if not colors:
            ttk.Label(parent, text="No colors yet.", foreground="#6b7280").grid(row=0, column=0, sticky="w")
            return

        max_columns = 8
        for index, color in enumerate(colors[: self.HISTORY_LIMIT]):
            row = index // max_columns
            column = index % max_columns
            button = tk.Button(
                parent,
                bg=color,
                activebackground=color,
                width=3,
                height=1,
                relief="flat",
                bd=0,
                command=lambda value=color: command(value),
            )
            button.grid(row=row, column=column, padx=4, pady=4)

    def _on_hsv_change(self, _value: str) -> None:
        if self._updating_sliders:
            return
        hex_value = self._hex_from_hsv()
        self.set_color(hex_value, add_to_history=False)

    def _commit_slider_color(self, _event) -> None:
        hex_value = self._hex_from_hsv()
        self.set_color(hex_value, add_to_history=True)

    def _hex_from_hsv(self) -> str:
        h = self.hue_var.get() / 360
        s = self.sat_var.get() / 100
        v = self.val_var.get() / 100
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return f"#{int(round(r * 255)):02X}{int(round(g * 255)):02X}{int(round(b * 255)):02X}"

    def _sync_sliders_from_rgb(self, rgb: tuple[int, int, int]) -> None:
        r, g, b = (channel / 255 for channel in rgb)
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        self._updating_sliders = True
        self.hue_var.set(int(round(h * 360)))
        self.sat_var.set(int(round(s * 100)))
        self.val_var.set(int(round(v * 100)))
        self._updating_sliders = False

    def _relative_luminance(self, rgb: tuple[int, int, int]) -> float:
        def channel_lum(channel: int) -> float:
            srgb = channel / 255
            return srgb / 12.92 if srgb <= 0.03928 else ((srgb + 0.055) / 1.055) ** 2.4

        r, g, b = (channel_lum(c) for c in rgb)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def _contrast_ratio(self, rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]) -> float:
        l1 = self._relative_luminance(rgb1)
        l2 = self._relative_luminance(rgb2)
        lighter, darker = (l1, l2) if l1 >= l2 else (l2, l1)
        return (lighter + 0.05) / (darker + 0.05)

    def _format_contrast_label(self, ratio: float) -> str:
        if ratio >= 7:
            return f"{ratio:.2f} (AAA)"
        if ratio >= 4.5:
            return f"{ratio:.2f} (AA)"
        return f"{ratio:.2f} (Fail)"

    def _update_contrast(self) -> None:
        rgb = self.current_color["rgb"]
        white = (255, 255, 255)
        black = (0, 0, 0)
        custom_rgb = self._hex_to_rgb(self.custom_background)

        white_ratio = self._contrast_ratio(rgb, white)
        black_ratio = self._contrast_ratio(rgb, black)
        custom_ratio = self._contrast_ratio(rgb, custom_rgb)

        self.contrast_white_var.set(f"White: {self._format_contrast_label(white_ratio)}")
        self.contrast_black_var.set(f"Black: {self._format_contrast_label(black_ratio)}")
        self.contrast_custom_var.set(f"Custom: {self._format_contrast_label(custom_ratio)}")

    def pick_custom_background(self) -> None:
        color = colorchooser.askcolor(initialcolor=self.custom_background, title="Pick background color")
        if color and color[1]:
            self.custom_background = color[1].upper()
            self.custom_bg_swatch.delete("all")
            self.custom_bg_swatch.create_rectangle(1, 1, 22, 16, fill=self.custom_background, outline="")
            self._update_contrast()
            self._set_status(f"Custom background set to {self.custom_background}.", duration=2000)

    def export_palette(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Export palette",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        )
        if not path:
            return

        payload = {"favorites": self.favorites, "history": self.history}
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(payload, file, indent=2)
            self._set_status(f"Exported palette to {path}.", duration=2500)
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export palette: {e}")

    def import_palette(self) -> None:
        path = filedialog.askopenfilename(title="Import palette", filetypes=[("JSON files", "*.json")])
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as file:
                payload = json.load(file)
            favorites = payload.get("favorites", [])
            history = payload.get("history", [])

            self.favorites = self._sanitize_palette(favorites)
            self.history = self._sanitize_palette(history)

            self.favorites_list.delete(0, tk.END)
            for color in self.favorites:
                self.favorites_list.insert(tk.END, color)
            self.history_list.delete(0, tk.END)
            for color in self.history:
                self.history_list.insert(tk.END, color)

            self._render_swatches(self.favorites_swatches, self.favorites, self.set_color)
            self._render_swatches(self.history_swatches, self.history, self.set_color)
            self._save_favorites()
            self._set_status("Imported palette successfully.", duration=2500)
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import palette: {e}")

    def _sanitize_palette(self, colors: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in colors:
            if not isinstance(value, str):
                continue
            hex_value = value.strip().upper()
            if not hex_value.startswith("#"):
                hex_value = f"#{hex_value}"
            if re.fullmatch(r"#([0-9A-F]{3}|[0-9A-F]{6})", hex_value):
                if len(hex_value) == 4:
                    hex_value = f"#{hex_value[1]*2}{hex_value[2]*2}{hex_value[3]*2}"
                if hex_value not in normalized:
                    normalized.append(hex_value)
        return normalized[: self.HISTORY_LIMIT]


if __name__ == "__main__":
    root = tk.Tk()
    app = ColorPickerApp(root)
    root.mainloop()
