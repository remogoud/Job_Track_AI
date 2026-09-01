"""
Job_Track_AI - Search filter model.

Encapsulates the user's job-search criteria (country, remote, salary, role,
keywords) and normalises them into the query shapes used by both API clients
and scrapers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pydantic import BaseModel, Field


# High-income target markets (spec: global search across top markets).
COUNTRIES: dict[str, str] = {
    "US": "United States",
    "UK": "United Kingdom",
    "Germany": "Germany",
    "Canada": "Canada",
    "Australia": "Australia",
    "Singapore": "Singapore",
    "UAE": "United Arab Emirates",
    "India": "India",
    "Remote": "Worldwide (Remote)",
}

# Sites the search can query.
SOURCES = ["linkedin", "indeed", "naukri", "glassdoor", "monster",
           "ziprecruiter", "generic"]

# Manual (guest) vs authenticated entry points (spec: support both).
ACCESS_MODES = ["guest", "authenticated"]


class SearchFilters(BaseModel):
    keywords: str = Field(default="", description="Role/keyword query, e.g. 'Sr. Data Engineer'")
    country: str = Field(default="US")
    remote_only: bool = Field(default=False)
    salary_min: int | None = Field(default=None)
    salary_max: int | None = Field(default=None)
    sources: list[str] = Field(default_factory=lambda: ["linkedin", "indeed"])
    access_mode: str = Field(default="guest")
    max_results: int = Field(default=25, ge=1, le=200)
    posted_within_days: int | None = Field(default=7)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.country not in COUNTRIES:
            errors.append(f"Unknown country '{self.country}'")
        for s in self.sources:
            if s not in SOURCES:
                errors.append(f"Unknown source '{s}'")
        if self.access_mode not in ACCESS_MODES:
            errors.append("access_mode must be guest or authenticated")
        if self.salary_min and self.salary_max and self.salary_min > self.salary_max:
            errors.append("salary_min must be <= salary_max")
        return errors

    def location_query(self) -> str:
        return COUNTRIES.get(self.country, "Worldwide")
