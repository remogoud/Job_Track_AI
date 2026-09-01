"""
Job_Track_AI — Human-like navigation simulator.

When a target site is known to run bot detection, the scraper routes through
this module which inserts realistic delays, scrolls in human steps, and simulates
cursor movement / clicks instead of hammering endpoints. When bot monitoring is
absent, the orchestrator sets `automation_speed="fast"` to skip these waits.

IMPORTANT LEGAL NOTE: live scraping of LinkedIn/Indeed/Glassdoor can violate
their Terms of Service and may lead to account suspension. This framework is
provided for API-based flows and for sites whose terms permit it. Real-site
scraping is DISABLED by default (settings.enable_scraping_real_sites=False).

The source of truth for which site is "human" vs "fast" lives in
SITE_BEHAVIOUR below.
"""
from __future__ import annotations

import random
import time
from typing import Callable

from config.settings import settings

# Which sites are treated as bot-monitored (human-like) vs fast.
SITE_BEHAVIOUR: dict[str, str] = {
    "linkedin": "human",
    "indeed": "human",
    "glassdoor": "human",
    "naukri": "human",
    "monster": "fast",
    "ziprecruiter": "fast",
    "remote": "fast",
    "generic": "fast",
}


class Humanizer:
    """Delivers a callable "pause" and scroll/click simulators per site."""

    def __init__(self, site: str = "generic"):
        self.site = site
        self.mode = SITE_BEHAVIOUR.get(site, "generic")
        self.enabled = settings.is_humanlike and self.mode == "human"

    def pause(self) -> float:
        """Sleep a human-like random delay. Returns the elapsed seconds."""
        if not self.enabled:
            return 0.0
        delay = random.uniform(settings.human_delay_min, settings.human_delay_max)
        time.sleep(delay)
        return delay

    def scroll(self, driver=None, total_steps: int | None = None) -> None:
        """Simulate incremental scrolling. Accepts a Selenium-like driver or a no-op."""
        if not self.enabled:
            time.sleep(random.uniform(0.05, 0.2))
            return
        steps = total_steps or settings.scroll_step
        for _ in range(steps):
            # random small jitter in scroll distance
            if driver is not None:
                try:
                    driver.execute_script(window.get_scroll_js())
                except Exception:
                    pass
            time.sleep(random.uniform(settings.human_delay_min / 2,
                                      settings.human_delay_max / 2))

    def click(self, click_fn: Callable[[], None] | None = None) -> None:
        """Simulate a human click (optional cursor movement + delay)."""
        if not self.enabled:
            if click_fn:
                click_fn()
            return
        time.sleep(random.uniform(settings.click_delay, settings.click_delay * 1.8))
        if click_fn:
            click_fn()

    # Convenience: expose scroll JS for selenium drivers.
    @staticmethod
    def scroll_js() -> str:
        return ("window.scrollBy({top: Math.floor((Math.random()*300)+150),"
                "behavior:'smooth'});")
