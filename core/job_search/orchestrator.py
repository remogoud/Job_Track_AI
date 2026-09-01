"""
Job_Track_AI - Job search orchestrator.

Routes each requested source to its preferred path:
  * API-first (LinkedIn Jobs API, Indeed API) when credentials exist,
  * else an adapter that uses human-like navigation (scraping) for
    bot-detected sites, or fast mode where monitoring is absent.

All results are normalized to Job objects and persisted via the repository.
"""
from __future__ import annotations

import logging

from config.settings import settings
from database import repository as repo
from database.models import Job, SystemLog
from core.job_search.filters import SearchFilters
from core.job_search.api_clients import LinkedInJobsAPI, IndeedJobsAPI
from core.job_search.site_adapters import ADAPTER_REGISTRY
from core.job_search.base_scraper import ScrapeResult

log = logging.getLogger(__name__)

# Map: preferred path for each source.
_API_SOURCES: dict[str, object] = {
    "linkedin": LinkedInJobsAPI,
    "indeed": IndeedJobsAPI,
}


class JobSearchOrchestrator:
    """Coordinates multi-source search + human-like vs fast navigation."""

    def __init__(self, filters: SearchFilters):
        self.filters = filters
        self.results: list[Job] = []
        self.methods_used: dict[str, str] = {}

    def run(self) -> list[Job]:
        errors = self.filters.validate()
        if errors:
            log.warning("Invalid filters: %s", errors)
            return []

        for source in self.filters.sources:
            method = self._search_source(source)
            self.methods_used[source] = method
        repo.log_action("job_search", {"sources": self.filters.sources,
                                       "method": self.methods_used})
        return self.results

    def _search_source(self, source: str) -> str:
        """Returns the method label used (api / human-like / fast)."""
        method = "fast"
        jobs: list[Job] = []

        # 1) Prefer API
        api_cls = _API_SOURCES.get(source)
        if api_cls:
            api = api_cls()
            jobs = api.search(self.filters)
            method = "api"

        # 2) Fall back to scraping adapter
        if not jobs and source in ADAPTER_REGISTRY:
            adapter = ADAPTER_REGISTRY[source](filters=self.filters)
            result: ScrapeResult = adapter.search()
            if result.ok and result.jobs:
                jobs = result.jobs
                method = "human-like" if adapter.humanizer.enabled else "fast"
            else:
                log.info("Source %s returned nothing (%s).", source, result.error)

        # 3) Persist + correlate
        for job in jobs:
            repo.create_job(job)
            self.results.append(job)
        return method
