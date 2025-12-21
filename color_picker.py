from __future__ import annotations

import colorsys
import re
import tkinter as tk
from tkinter import colorchooser, messagebox, ttk


class ColorPickerApp:
    """Enhanced color picker helper with history, copying, and live preview."""

    HISTORY_LIMIT = 10

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("🎨 Color Picker")
        self.root.geometry("480x520")
        self.root.minsize(360, 320)
        self.root.resizable(True, True)

        self._status_after_id: str | None = None
        self.current_color = {"hex": "#3498DB", "rgb": (52, 152, 219)}
        self.history: list[str] = []

        self._build_ui()
        self.set_color(self.current_color["hex"], add_to_history=False)
        self._set_status("Pick a color to get started.")

    def _build_ui(self) -> None:
        style = ttk.Style(self.root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 11))

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

        preview_frame = ttk.LabelFrame(self.main_frame, text="Preview", padding=15)
        preview_frame.grid(row=0, column=0, sticky="ew")
        preview_frame.columnconfigure(0, weight=1)

        self.preview = tk.Canvas(preview_frame, width=200, height=110, highlightthickness=0, bd=0)
        self.preview_rect = self.preview.create_rectangle(
            2, 2, 198, 108, outline="#d1d5db", width=1, fill=self.current_color["hex"]
        )
        self.preview.pack()

        info_frame = ttk.LabelFrame(self.main_frame, text="Color values", padding=15)
        info_frame.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        info_frame.columnconfigure(0, weight=1)

        self.hex_display = tk.StringVar(value="HEX: #------")
        self.rgb_display = tk.StringVar(value="RGB: (---, ---, ---)")
        self.hsl_display = tk.StringVar(value="HSL: (---°, ---, ---)")

        ttk.Label(info_frame, textvariable=self.hex_display, font=("Consolas", 13)).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Label(info_frame, textvariable=self.rgb_display, font=("Consolas", 13)).grid(
            row=1, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Label(info_frame, textvariable=self.hsl_display, font=("Consolas", 13)).grid(
            row=2, column=0, sticky="w"
        )

        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        control_frame.columnconfigure((0, 1, 2), weight=1)

        ttk.Button(control_frame, text="Pick a Color", command=self.pick_color).grid(
            row=0, column=0, padx=(0, 8), sticky="ew"
        )
        ttk.Button(control_frame, text="Copy HEX", command=lambda: self.copy_to_clipboard(self.current_color["hex"], "HEX")).grid(
            row=0, column=1, padx=4, sticky="ew"
        )
        ttk.Button(
            control_frame,
            text="Copy RGB",
            command=lambda: self.copy_to_clipboard(self._format_rgb(self.current_color["rgb"]), "RGB"),
        ).grid(row=0, column=2, padx=(8, 0), sticky="ew")

        manual_frame = ttk.LabelFrame(self.main_frame, text="Manual HEX input", padding=15)
        manual_frame.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        manual_frame.columnconfigure(1, weight=1)

        ttk.Label(manual_frame, text="Enter HEX (#RGB/RRGGBB):").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.hex_entry_var = tk.StringVar()
        self.hex_entry = ttk.Entry(manual_frame, textvariable=self.hex_entry_var, font=("Consolas", 12), width=14)
        self.hex_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        ttk.Button(manual_frame, text="Apply", command=self.apply_hex_input).grid(row=0, column=2)

        history_frame = ttk.LabelFrame(self.main_frame, text="Recent colors (double-click to reuse)", padding=15)
        history_frame.grid(row=4, column=0, sticky="nsew", pady=(16, 0))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(1, weight=1)

        self.history_list = tk.Listbox(history_frame, height=6, activestyle="none", font=("Consolas", 12))
        self.history_list.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_list.yview)
        scrollbar.grid(row=1, column=1, sticky="nsw", padx=(6, 0))
        self.history_list.configure(yscrollcommand=scrollbar.set)
        self.history_list.bind("<Double-Button-1>", self.on_history_select)

        status_frame = ttk.Frame(self.main_frame, padding=(0, 8, 0, 0))
        status_frame.grid(row=5, column=0, sticky="ew")
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 10), foreground="#555555").grid(
            row=0, column=0, sticky="w"
        )

    def pick_color(self) -> None:
        color = colorchooser.askcolor(initialcolor=self.current_color["hex"], title="Pick a color")
        if color and color[1]:
            self.set_color(color[1].upper())
        else:
            self._set_status("Color selection canceled.", duration=2000)

    def apply_hex_input(self) -> None:
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

    def set_color(self, hex_value: str, add_to_history: bool = True) -> None:
        rgb = tuple(int(hex_value[i : i + 2], 16) for i in (1, 3, 5))
        self.current_color = {"hex": hex_value, "rgb": rgb}
        self.hex_entry_var.set(hex_value)

        self.preview.itemconfig(self.preview_rect, fill=hex_value)
        self.hex_display.set(f"HEX: {hex_value}")
        self.rgb_display.set(f"RGB: {self._format_rgb(rgb)}")
        self.hsl_display.set(f"HSL: {self._format_hsl(rgb)}")

        if add_to_history:
            self._update_history(hex_value)
        self._set_status(f"Current color set to {hex_value}.", duration=2200)

    def _update_history(self, hex_value: str) -> None:
        if hex_value in self.history:
            self.history.remove(hex_value)
        self.history.insert(0, hex_value)
        self.history = self.history[: self.HISTORY_LIMIT]

        self.history_list.delete(0, tk.END)
        for color in self.history:
            self.history_list.insert(tk.END, color)

    def on_history_select(self, event) -> None:
        selection = self.history_list.curselection()
        if not selection:
            return
        hex_value = self.history_list.get(selection[0])
        self.set_color(hex_value)

    def copy_to_clipboard(self, value: str, label: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self._set_status(f"{label} copied to clipboard.", duration=2000)

    def _format_rgb(self, rgb: tuple[int, int, int]) -> str:
        return f"{rgb[0]}, {rgb[1]}, {rgb[2]}"

    def _format_hsl(self, rgb: tuple[int, int, int]) -> str:
        r, g, b = (channel / 255 for channel in rgb)
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return f"{int(round(h * 360))}°, {int(round(s * 100))}%, {int(round(l * 100))}%"

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


if __name__ == "__main__":
    root = tk.Tk()
    app = ColorPickerApp(root)
    root.mainloop()
