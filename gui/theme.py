"""
Job_Track_AI - Nexacore Dark Theme & Styling System.

Centralized styling system defining the Nexacore dark color palette,
modern typography hierarchy, and ttk widget style rules for the
desktop interface.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# Nexacore Dark Color Palette
COLORS = {
    "bg_dark": "#0B0F19",       # Deep navy background
    "bg_surface": "#111827",    # Main panel / container surface
    "bg_card": "#1F2937",       # Card / subsection background
    "bg_input": "#111827",      # Input field background
    "border": "#374151",        # Subtle element border
    "border_focus": "#06B6D4",  # Cyan focus border
    "text_main": "#F9FAFB",     # High-contrast white text
    "text_muted": "#9CA3AF",    # Secondary muted text
    "text_dim": "#6B7280",      # Tertiary dim text
    "accent_cyan": "#06B6D4",   # Primary accent cyan
    "accent_cyan_hover": "#22D3EE",
    "accent_violet": "#8B5CF6", # Secondary accent violet
    "accent_violet_hover": "#A78BFA",
    "accent_blue": "#3B82F6",
    "success": "#10B981",       # Emerald green
    "warning": "#F59E0B",       # Amber
    "danger": "#EF4444",        # Crimson
    "tab_active": "#1F2937",    # Active tab background
    "tab_inactive": "#0F172A",  # Inactive tab background
}

# Modern Typography Scale
FONTS = {
    "family": "Segoe UI",
    "title": ("Segoe UI", 16, "bold"),
    "h1": ("Segoe UI", 13, "bold"),
    "h2": ("Segoe UI", 11, "bold"),
    "body": ("Segoe UI", 10),
    "body_bold": ("Segoe UI", 10, "bold"),
    "small": ("Segoe UI", 9),
    "mono": ("Consolas", 10),
}


def apply_theme(root: tk.Tk) -> None:
    """
    Apply the Nexacore dark theme across all Tkinter and TTK widgets.
    Configures background colors, ttk element styles, and entry defaults.
    """
    root.configure(bg=COLORS["bg_dark"])

    style = ttk.Style(root)
    # Use clam as baseline engine for flexible dark mode recoloring
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # Global TTK defaults
    style.configure(".",
                    background=COLORS["bg_surface"],
                    foreground=COLORS["text_main"],
                    font=FONTS["body"],
                    borderwidth=0)

    # Main Containers & Frames
    style.configure("TFrame", background=COLORS["bg_surface"])
    style.configure("Dark.TFrame", background=COLORS["bg_dark"])
    style.configure("Card.TFrame", background=COLORS["bg_card"])

    # Labels
    style.configure("TLabel",
                    background=COLORS["bg_surface"],
                    foreground=COLORS["text_main"],
                    font=FONTS["body"])
    style.configure("Title.TLabel",
                    font=FONTS["title"],
                    foreground=COLORS["text_main"],
                    background=COLORS["bg_dark"])
    style.configure("Header.TLabel",
                    font=FONTS["h1"],
                    foreground=COLORS["accent_cyan"],
                    background=COLORS["bg_surface"])
    style.configure("Muted.TLabel",
                    font=FONTS["small"],
                    foreground=COLORS["text_muted"],
                    background=COLORS["bg_surface"])

    # Notebook Tabs
    style.configure("TNotebook",
                    background=COLORS["bg_dark"],
                    borderwidth=0,
                    tabmargins=[2, 5, 2, 0])
    style.configure("TNotebook.Tab",
                    background=COLORS["tab_inactive"],
                    foreground=COLORS["text_muted"],
                    font=FONTS["body_bold"],
                    padding=[14, 6],
                    borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", COLORS["tab_active"]), ("active", COLORS["bg_card"])],
              foreground=[("selected", COLORS["accent_cyan"]), ("active", COLORS["text_main"])])

    # Standard Buttons
    style.configure("TButton",
                    background=COLORS["bg_card"],
                    foreground=COLORS["text_main"],
                    font=FONTS["body_bold"],
                    padding=[10, 5],
                    borderwidth=1,
                    relief="flat")
    style.map("TButton",
              background=[("active", COLORS["accent_cyan"]), ("pressed", COLORS["accent_violet"])],
              foreground=[("active", COLORS["bg_dark"]), ("pressed", COLORS["text_main"])])

    # Accent Cyan Button
    style.configure("Accent.TButton",
                    background=COLORS["accent_cyan"],
                    foreground=COLORS["bg_dark"],
                    font=FONTS["body_bold"],
                    padding=[12, 6],
                    borderwidth=0)
    style.map("Accent.TButton",
              background=[("active", COLORS["accent_cyan_hover"]), ("pressed", COLORS["accent_violet"])],
              foreground=[("active", COLORS["bg_dark"]), ("pressed", COLORS["text_main"])])

    # Accent Violet Button
    style.configure("Violet.TButton",
                    background=COLORS["accent_violet"],
                    foreground=COLORS["text_main"],
                    font=FONTS["body_bold"],
                    padding=[12, 6],
                    borderwidth=0)
    style.map("Violet.TButton",
              background=[("active", COLORS["accent_violet_hover"]), ("pressed", COLORS["accent_cyan"])])

    # Entry & Combobox
    style.configure("TEntry",
                    fieldbackground=COLORS["bg_input"],
                    foreground=COLORS["text_main"],
                    insertcolor=COLORS["accent_cyan"],
                    borderwidth=1,
                    relief="solid")
    style.configure("TCombobox",
                    fieldbackground=COLORS["bg_input"],
                    background=COLORS["bg_card"],
                    foreground=COLORS["text_main"],
                    arrowcolor=COLORS["accent_cyan"],
                    borderwidth=1)
    style.map("TCombobox",
              fieldbackground=[("readonly", COLORS["bg_input"])],
              foreground=[("readonly", COLORS["text_main"])])

    # Treeview / Tables
    style.configure("Treeview",
                    background=COLORS["bg_card"],
                    foreground=COLORS["text_main"],
                    fieldbackground=COLORS["bg_card"],
                    font=FONTS["body"],
                    borderwidth=0,
                    rowheight=26)
    style.configure("Treeview.Heading",
                    background=COLORS["bg_surface"],
                    foreground=COLORS["accent_cyan"],
                    font=FONTS["body_bold"],
                    borderwidth=1)
    style.map("Treeview",
              background=[("selected", COLORS["accent_violet"])],
              foreground=[("selected", COLORS["text_main"])])

    # Scrollbars
    style.configure("Vertical.TScrollbar",
                    background=COLORS["bg_card"],
                    troughcolor=COLORS["bg_dark"],
                    bordercolor=COLORS["bg_dark"],
                    arrowcolor=COLORS["text_muted"])

    # LabelFrames / Group Boxes
    style.configure("TLabelframe",
                    background=COLORS["bg_surface"],
                    bordercolor=COLORS["border"],
                    borderwidth=1)
    style.configure("TLabelframe.Label",
                    background=COLORS["bg_surface"],
                    foreground=COLORS["accent_cyan"],
                    font=FONTS["h2"])
