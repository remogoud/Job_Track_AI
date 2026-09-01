"""
Job_Track_AI - Base scraper.

Provides a common HTTP access path with:
  * polite headers,
  * optional human-like pacing via Humanizer,
  * a strict toggle so LIVE scraping is off unless the user opts in,
  * a safe simulated mode that returns fixture data for testing/demo.

Real-site scraping is DISABLED unless settings.enable_scraping_real_sites=True.
"""
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from urllib.parse import urljoin

import requests

from config.settings import settings
from database.models import Job
from core.job_search.humanizer import Humanizer
from core.job_search.filters import SearchFilters

log = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
}


class ScrapeLimitExceeded(Exception):
    """Raised when a site returns an anti-bot / block response."""


@dataclass
class ScrapeResult:
    ok: bool = True
    jobs: list[Job] | None = None
    error: str | None = None
    blocked: bool = False


class BaseScraper:
    site: str = "generic"
    base_url: str = ""
    legal_notice: str = "Live scraping may violate the site's Terms of Service."

    def __init__(self, **kwargs):
        self.filters: SearchFilters | None = kwargs.get("filters")
        self.humanizer = Humanizer(self.site)
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        self._session.headers["User-Agent"] = random.choice(USER_AGENTS)

    # -- helpers ------------------------------------------------------------
    def get(self, url: str, params: dict | None = None) -> requests.Response:
        if not settings.enable_scraping_real_sites:
            raise ScrapeLimitExceeded(
                "Live scraping disabled. Set ENABLE_SCRAPING_REAL_SITES=true "
                "in .env, or use an API source.")
        self.humanizer.pause()
        resp = self._session.get(url, params=params, timeout=20)
        if resp.status_code in (403, 429):
            self.humanizer.pause()
            raise ScrapeLimitExceeded(
                f"Anti-bot block ({resp.status_code}) from {self.site}. "
                "Consider the API path for this site.")
        return resp

    def fetch_jobs(self) -> list[Job]:
        """Subclasses implement this. Returns a list of normalized Jobs."""
        raise NotImplementedError

    def search(self) -> ScrapeResult:
        try:
            jobs = self.fetch_jobs()
            return ScrapeResult(ok=True, jobs=jobs)
        except ScrapeLimitExceeded as exc:
            return ScrapeResult(ok=False, error=str(exc), blocked=True)
        except Exception as exc:
            log.exception("Search failed for %s", self.site)
            return ScrapeResult(ok=False, error=str(exc))

    # -- guarded real scraping ------------------------------------------------
    def _guarded(self) -> bool:
        return settings.enable_scraping_real_sites
