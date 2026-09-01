"""
Job_Track_AI - User-facing configuration manager.

Wraps the immutable `Settings` dataclass with load/save operations so the GUI
can persist runtime preferences (automation speed, toggles, thresholds) to a
user-owned `config.json` next to the database. Nothing here touches secrets.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config.settings import settings, Settings


class ConfigManager:
    """Loads and saves user-adjustable runtime configuration."""

    def __init__(self, config_path: Path | None = None):
        self.path = config_path or (settings.project_root / "data" / "config.json")
        self._data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any, persist: bool = True) -> None:
        self._data[key] = value
        if persist:
            self.save()

    def editable(self) -> dict[str, Any]:
        """Key preferences the GUI exposes to the user."""
        return {
            "automation_speed": {
                "value": self.get("automation_speed", settings.automation_speed),
                "options": ["human", "fast"],
                "help": "human = human-like delays/scroll/clicks; fast = no waits",
            },
            "match_threshold": {
                "value": self.get("match_threshold", settings.match_threshold),
                "help": "Minimum match score to proceed (>= 0.77 by default).",
            },
            "enable_scraping_real_sites": {
                "value": self.get(
                    "enable_scraping_real_sites", settings.enable_scraping_real_sites),
                "help": "DANGER: live scraping of LinkedIn/Indeed may violate ToS",
            },
            "enable_voice": {
                "value": self.get("enable_voice", settings.enable_voice),
                "help": "Jarvis-style voice assistant mode.",
            },
            "enable_notifications": {
                "value": self.get(
                    "enable_notifications", settings.enable_notifications),
                "help": "Desktop + calendar follow-up notifications.",
            },
        }
