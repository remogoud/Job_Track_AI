"""
Job_Track_AI — Shared Tkinter widget helpers.

Lightweight helpers to keep the main app module readable. Uses only the stdlib
Tkinter UI so the packaged .exe has no heavyweight GUI framework dependency.
"""
from __future__ import annotations

from tkinter import ttk


class ScrolledText(ttk.Frame):
    """A labeled multi-line text area with a scrollbar."""
    def __init__(self, master, label: str, height=8, **kw):
        super().__init__(master)
        self.label = ttk.Label(self, text=label)
        self.label.pack(anchor="w", pady=(4, 0))
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)
        self.text_frame = frame
        self.text = __import__("tkinter").Text(
            frame, height=height, wrap="word", **kw)
        self.scroll = ttk.Scrollbar(frame, orient="vertical",
                                    command=self.text.yview)
        self.text.configure(yscrollcommand=self.scroll.set)
        self.scroll.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

    def set(self, value: str) -> None:
        self.text.delete("1.0", "end")
        self.text.insert("1.0", value or "")

    def get(self) -> str:
        return self.text.get("1.0", "end").strip()


def add_scroll(parent):
    """Return (canvas, frame) for a scrollable container."""
    import tkinter as tk
    canvas = tk.Canvas(parent)
    scroll = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    inner = ttk.Frame(canvas)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    return canvas, inner
