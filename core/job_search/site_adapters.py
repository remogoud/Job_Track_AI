"""
Job_Track_AI — Per-site adapters for scraping (human-like) paths.

Each adapter maps a site's page markup into normalized Job objects. The
`humanize` flag controls whether the Humanizer (delays/scrolls/clicks) is used.
Adaptive speed: bot-detected sites use human-like navigation; monitored-lite
sites run at "fast".

Note: These adapters require settings.enable_scraping_real_sites=True to reach
the network (OFF by default due to ToS risk). They also expose a `simulate`
mode so the pipeline works offline.
"""
from __future__ import annotations

import logging
from typing import Callable

from bs4 import BeautifulSoup

from database.models import Job
from core.job_search.base_scraper import BaseScraper
from core.job_search.filters import SearchFilters
from core.job_search.humanizer import SITE_BEHAVIOUR

log = logging.getLogger(__name__)


class _ParsingMixin:
    """Shared extraction heuristics to map raw markup into Job fields."""

    @staticmethod
    def text(soup: BeautifulSoup, selectors: list[str]) -> str:
        for sel in selectors:
            node = soup.select_one(sel)
            if node and node.get_text(strip=True):
                return node.get_text(strip=True)
        return ""

    @staticmethod
    def parse_from_blocks(blocks: list[dict]) -> list[Job]:
        jobs = []
        for b in blocks:
            if not b.get("title"):
                continue
            jobs.append(Job(
                title=b.get("title", ""),
                company=b.get("company", ""),
                location=b.get("location", ""),
                salary_range=b.get("salary_range", ""),
                description=b.get("description", ""),
                source=b.get("source", "generic"),
                match_score=float(b.get("match_score", 0.0)),
            ))
        return jobs


class LinkedInAdapter(BaseScraper, _ParsingMixin):
    site = "linkedin"
    base_url = "https://www.linkedin.com/jobs"

    def fetch_jobs(self) -> list[Job]:
        if self.filters is None:
            return []
        if not self._guarded():
            raise self.ScrapeLimitExceeded(
                "LinkedIn live scraping is disabled (ToS risk). Use the LinkedIn "
                "Jobs API (core/job_search/api_clients.py) instead.")
        url = f"{self.base_url}/search?keywords={self.filters.keywords}&location={self.filters.location_query()}"
        resp = self.get(url)
        return self._extract(resp.text)

    def _extract(self, html: str) -> list[Job]:
        soup = BeautifulSoup(html, "html.parser")
        # Real LinkedIn markup is heavily obfuscated + session-gated; this is an
        # illustrative parser for the post-login DOM. Logged-in scraping requires
        # an authenticated session (Cookies/0Auth) and MUST use API when possible.
        jobs: list[Job] = []
        for card in soup.select("li.base-card, li.job-card-container")[: self.filters.max_results]:
            jobs.append(Job(
                title=self.text(card, ["h3.base-search-card__title", "h3"]),
                company=self.text(card, ["h4.base-search-card__subtitle"]),
                location=self.text(card, ["span.job-search-card__location"]),
                source="linkedin",
            ))
        return jobs


class NaukriAdapter(BaseScraper, _ParsingMixin):
    site = "naukri"
    base_url = "https://www.naukri.com"

    def fetch_jobs(self) -> list[Job]:
        if self.filters is None:
            return []
        if not self._guarded():
            return _sim(self.filters, "naukri", self.humanizer)
        resp = self.get(
            f"{self.base_url}/job-listings-{self.filters.keywords.replace(' ', '-')}",
            params={"location": self.filters.location_query()})
        return self._extract(resp.text)

    def _extract(self, html: str) -> list[Job]:
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        for card in soup.select("div.jobTuple, div.row")[: self.filters.max_results]:
            jobs.append(Job(
                title=self.text(card, ["a.title", "h3"]),
                company=self.text(card, ["a.subTitle", "span.subTitle"]),
                location=self.text(card, ["span.locWrap"]),
                source="naukri",
            ))
        return jobs


class GenericAdapter(BaseScraper, _ParsingMixin):
    """Fallback for niche portals. Runs at 'fast' speed (no bot monitoring)."""
    site = "generic"
    base_url = ""

    def fetch_jobs(self) -> list[Job]:
        if self.filters is None:
            return []
        if not self._guarded():
            return _sim(self.filters, "generic", self.humanizer)
        raise ScrapeLimitExceeded(
            "Generic scraping requires an explicit base_url for the target portal.")


def _sim(filters: SearchFilters, source: str, humanizer) -> list[Job]:
    """Simulated result set so the pipeline runs offline."""
    from core.job_search.api_clients import _simulate_jobs
    humanizer.pause()
    return _simulate_jobs(source, filters)


class IndeedAdapter(BaseScraper, _ParsingMixin):
    site = "indeed"
    base_url = "https://www.indeed.com"

    def fetch_jobs(self) -> list[Job]:
        from core.job_search.base_scraper import ScrapeLimitExceeded
        if self.filters is None:
            return []
        if not self._guarded():
            return _sim(self.filters, "indeed", self.humanizer)
        raise ScrapeLimitExceeded(
            "Indeed live scraping is disabled (ToS risk). Use the Indeed API "
            "(core/job_search/api_clients.py) or a partner feed instead.")


# Registry: site name -> adapter class. "fast"/"human" behaviour is derived
# automatically from SITE_BEHAVIOUR / automation_speed setting.
ADAPTER_REGISTRY: dict[str, type[BaseScraper]] = {
    "linkedin": LinkedInAdapter,
    "indeed": IndeedAdapter,
    "naukri": NaukriAdapter,
    "generic": GenericAdapter,
    "glassdoor": GenericAdapter,   # gated; API preferred
    "monster": GenericAdapter,     # low monitoring -> runs fast
    "ziprecruiter": GenericAdapter,# runs fast
}
