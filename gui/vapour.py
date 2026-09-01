"""
Job_Track_AI - Vapour Particle Heading Banner.

Provides a particle-based vapour text heading effect on top of the
application window, creating a subtle glowing cyan/violet particle
animation around the title text.
"""
from __future__ import annotations

import math
import random
import tkinter as tk
from gui.theme import COLORS, FONTS

# Tunables for the particle effect
PARTICLE_DENSITY = 24       # Number of simultaneous floating particles (0 to disable)
PARTICLE_SPEED = 0.8        # Float speed
PARTICLE_LIFE = 60          # Frame lifetime per particle


class VapourParticle:
    """Individual particle in the vapour canvas effect."""
    def __init__(self, x: float, y: float, canvas_width: int, canvas_height: int):
        self.canvas_w = canvas_width
        self.canvas_h = canvas_height
        self.reset(x, y)

    def reset(self, x: float = None, y: float = None) -> None:
        self.x = x if x is not None else random.uniform(20, max(40, self.canvas_w - 20))
        self.y = y if y is not None else random.uniform(10, max(20, self.canvas_h - 10))
        self.vx = random.uniform(-0.4, 0.4) * PARTICLE_SPEED
        self.vy = random.uniform(-0.6, -0.1) * PARTICLE_SPEED
        self.size = random.uniform(1.5, 3.5)
        self.life = random.randint(20, PARTICLE_LIFE)
        self.max_life = self.life
        self.color = random.choice([COLORS["accent_cyan"], COLORS["accent_violet"], "#38BDF8", "#C084FC"])

    def update(self) -> None:
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.life <= 0 or self.y < 0 or self.x < 0 or self.x > self.canvas_w:
            self.reset()


class VapourHeading(tk.Canvas):
    """
    Subtle particle vapour banner widget displaying the title with glowing particles.
    """
    def __init__(self, master, title: str = "JOB_TRACK_AI", subtitle: str = "AI-Driven Career Automation Engine", height: int = 58, **kw):
        super().__init__(master, height=height, bg=COLORS["bg_dark"], highlightthickness=0, **kw)
        self.title_text = title
        self.subtitle_text = subtitle
        self.particles: list[VapourParticle] = []
        self._running = False
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event) -> None:
        w = max(event.width, 100)
        h = max(event.height, 40)
        if PARTICLE_DENSITY > 0 and len(self.particles) == 0:
            self.particles = [VapourParticle(random.uniform(20, w - 20), random.uniform(10, h - 10), w, h) for _ in range(PARTICLE_DENSITY)]
        else:
            for p in self.particles:
                p.canvas_w = w
                p.canvas_h = h
        self._render()

    def start(self) -> None:
        """Start the animation loop."""
        if not self._running and PARTICLE_DENSITY > 0:
            self._running = True
            self._animate()

    def stop(self) -> None:
        """Stop the animation loop."""
        self._running = False

    def _animate(self) -> None:
        if not self._running:
            return
        for p in self.particles:
            p.update()
        self._render()
        self.after(50, self._animate)

    def _render(self) -> None:
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1:
            w = 1000
        if h <= 1:
            h = 58

        # Draw subtle bottom glow line
        self.create_line(0, h - 1, w, h - 1, fill=COLORS["border"], width=1)
        self.create_line(w * 0.1, h - 1, w * 0.9, h - 1, fill=COLORS["accent_cyan"], width=1)

        # Draw particles
        for p in self.particles:
            alpha_factor = p.life / p.max_life
            if alpha_factor > 0.1:
                r = p.size
                self.create_oval(p.x - r, p.y - r, p.x + r, p.y + r, fill=p.color, outline="")

        # Draw Title with subtle shadow
        self.create_text(22, h // 2 - 6, text=self.title_text, font=FONTS["title"], fill=COLORS["bg_card"], anchor="w")
        self.create_text(20, h // 2 - 8, text=self.title_text, font=FONTS["title"], fill=COLORS["text_main"], anchor="w")
        # Subtitle
        self.create_text(220, h // 2 - 6, text=f"|  {self.subtitle_text}", font=FONTS["small"], fill=COLORS["text_muted"], anchor="w")

        # Right-aligned badge
        self.create_text(w - 20, h // 2 - 7, text="v1.0.0 Pro", font=FONTS["body_bold"], fill=COLORS["accent_cyan"], anchor="e")
