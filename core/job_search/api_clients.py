"""
Job_Track_AI - API-first job clients (LinkedIn, Indeed).

These are the PREFERRED paths for future-proofing: partner/exposed APIs return
structured, ToS-compliant payloads and avoid scraping risk. Where a real API
token isn't configured, the client falls back to a documented simulated mode so
the pipeline remains testable end-to-end.

Secrets come from security.secrets; never hard-coded.
"""
from __future__ import annotations

import logging

from config.settings import settings
from database.models import Job
from core.job_search.filters import SearchFilters
from security.secrets import get_secret, has_secret

log = logging.getLogger(__name__)


class LinkedInJobsAPI:
    """LinkedIn Jobs API (partner access). Requires OAuth access token."""

    def __init__(self):
        self.token = get_secret("LINKEDIN_ACCESS_TOKEN")

    @property
    def available(self) -> bool:
        return bool(self.token)

    def search(self, filters: SearchFilters) -> list[Job]:
        if not self.available:
            log.info("LinkedIn API token missing - using simulated results.")
            return _simulate_jobs("linkedin", filters)
        # Real implementation placeholder: authenticated GET to the Jobs API.
        # headers = {"Authorization": f"Bearer {self.token}"}
        # resp = requests.get(...)
        # parse into Job objects
        raise NotImplementedError("Wire your LinkedIn partner API endpoint here. "
                                  "See docs/DEPENDENCIES.md.")


class IndeedJobsAPI:
    """Indeed API (partner access). Requires client id/secret + publisher id."""

    def __init__(self):
        self.publisher_id = get_secret("INDEED_PUBLISHER_ID")

    @property
    def available(self) -> bool:
        return bool(self.publisher_id)

    def search(self, filters: SearchFilters) -> list[Job]:
        if not self.available:
            log.info("Indeed API key missing - using simulated results.")
            return _simulate_jobs("indeed", filters)
        raise NotImplementedError("Wire your Indeed partner API endpoint here. "
                                  "See docs/DEPENDENCIES.md.")


# ---------------------------------------------------------------------------
# Simulated / offline mode
# ---------------------------------------------------------------------------
_TITLES = ["Senior Data Engineer", "Full-Stack Developer", "Machine Learning Engineer",
           "DevOps Engineer", "Product Manager", "Backend Engineer"]
_COMPANIES = ["Northstar Systems", "Helios Labs", "Aurora Cloud", "Beacon Analytics",
              "Vertex Group", "Lumen Health"]
_COUNTRIES = {"US": "San Francisco, CA", "Germany": "Berlin, Germany",
              "UK": "London, UK", "India": "Hyderabad, India", "Remote": "Remote"}


def _simulate_jobs(source: str, filters: SearchFilters) -> list[Job]:
    """Deterministic-but-varied fixture generator for offline testing/demo."""
    import random
    rng = random.Random(hash((source, filters.keywords, filters.country)) % 2**32)
    jobs: list[Job] = []
    n = min(filters.max_results, 12)
    for _ in range(n):
        title = filters.keywords or rng.choice(_TITLES)
        loc = _COUNTRIES.get(filters.country, "Remote")
        jobs.append(Job(
            title=title,
            company=rng.choice(_COMPANIES),
            location=f"{loc} {'(Remote)' if filters.remote_only else ''}".strip(),
            salary_range=f"$ {rng.randint(90, 180)}k - {rng.randint(181, 320)}k",
            description=_sample_description(title),
            source=source,
        ))
    return jobs


def _sample_description(title: str) -> str:
    return (
        f"About the role: {title} responsible for architecting, building and "
        "maintaining robust solutions. == KEYWORDS == Python, SQL, Cloud, "
        "CI/CD, Agile, System Design, Problem Solving, Leadership == "
        "Requirements: 5+ years experience, strong communication."
    )
