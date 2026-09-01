"""
Job_Track_AI - Shared Tkinter & Nexacore widget components.

Provides reusable UI components: ScrolledText, Card containers,
NeoButton (custom rounded/accent action buttons), and scroll helpers.
Uses stdlib Tkinter/TTK for zero-dependency native desktop performance.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from gui.theme import COLORS, FONTS


class Card(ttk.Frame):
    """
    A styled dark card container with rounded/bordered visual style for section grouping.
    """
    def __init__(self, master, padding: int = 10, **kw):
        super().__init__(master, style="Card.TFrame", padding=padding, **kw)


class NeoButton(tk.Canvas):
    """
    A modern styled action button with subtle rounded corners and hover glow effects.
    """
    def __init__(
        self,
        master,
        text: str,
        command=None,
        width: int = 130,
        height: int = 34,
        bg_color: str = COLORS["accent_cyan"],
        hover_color: str = COLORS["accent_cyan_hover"],
        text_color: str = COLORS["bg_dark"],
        font=FONTS["body_bold"],
        radius: int = 6,
        **kw
    ):
        parent_bg = COLORS["bg_card"] if (hasattr(master, "_name") and "card" in str(master).lower()) else COLORS["bg_surface"]
        try:
            if hasattr(master, "cget") and not isinstance(master, ttk.Widget):
                parent_bg = master.cget("bg")
        except Exception:
            pass
        super().__init__(master, width=width, height=height, bg=parent_bg, highlightthickness=0, **kw)
        self.text = text
        self.command = command
        self.w = width
        self.h = height
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = font
        self.radius = radius
        self.is_hovered = False

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self._draw()

    def _draw_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _draw(self) -> None:
        self.delete("all")
        current_bg = self.hover_color if self.is_hovered else self.bg_color
        # Draw background capsule/rounded rect
        self._draw_rounded_rect(2, 2, self.w - 2, self.h - 2, self.radius, fill=current_bg, outline="")
        # Draw text label centered
        self.create_text(self.w // 2, self.h // 2, text=self.text, fill=self.text_color, font=self.font)

    def _on_enter(self, _event) -> None:
        self.is_hovered = True
        self._draw()

    def _on_leave(self, _event) -> None:
        self.is_hovered = False
        self._draw()

    def _on_click(self, _event) -> None:
        if self.command:
            self.command()


class ScrolledText(ttk.Frame):
    """A labeled multi-line text area with theme colors and smooth scrollbar."""
    def __init__(self, master, label: str, height: int = 8, **kw):
        super().__init__(master)
        if label:
            self.label = ttk.Label(self, text=label, font=FONTS["body_bold"])
            self.label.pack(anchor="w", pady=(4, 2))
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)
        self.text_frame = frame
        self.text = tk.Text(
            frame,
            height=height,
            wrap="word",
            bg=COLORS["bg_input"],
            fg=COLORS["text_main"],
            insertbackground=COLORS["accent_cyan"],
            selectbackground=COLORS["accent_violet"],
            selectforeground=COLORS["text_main"],
            font=FONTS["mono"],
            relief="solid",
            borderwidth=1,
            highlightthickness=0,
            **kw
        )
        self.scroll = ttk.Scrollbar(frame, orient="vertical",
                                    command=self.text.yview,
                                    style="Vertical.TScrollbar")
        self.text.configure(yscrollcommand=self.scroll.set)
        self.scroll.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

    def set(self, value: str) -> None:
        self.text.delete("1.0", "end")
        self.text.insert("1.0", value or "")

    def get(self) -> str:
        return self.text.get("1.0", "end").strip()


def add_scroll(parent):
    """Return (canvas, frame) for a scrollable dark container."""
    canvas = tk.Canvas(parent, bg=COLORS["bg_surface"], highlightthickness=0)
    scroll = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
    inner = ttk.Frame(canvas)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    return canvas, inner
