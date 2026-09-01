"""
Job_Track_AI — Agentic/MCP agents.

Each agent owns one capability (resume rewriting, cover letter drafting, job
search filtering) and exposes a `handle(message)` method so an orchestrator can
route natural-language requests to the right agent. This mirrors an MCP-style
tool registry: think of each agent as an MCP tool server.

Agents use the same local services as the GUI, so results persist to SQLite and
follow the approval workflow.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from database import repository as repo
from core.resume_engine.service import ResumeService
from core.cover_letter.service import CoverLetterService
from core.job_search.filters import SearchFilters
from core.job_search.orchestrator import JobSearchOrchestrator

log = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    agent: str
    ok: bool
    message: str
    data: Any = None


class BaseAgent:
    name = "base"

    def handle(self, message: str) -> AgentResponse:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 1) Resume rewriting agent
# ---------------------------------------------------------------------------
class ResumeAgent(BaseAgent):
    name = "resume_rewrite"

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.service = ResumeService(user_id)

    def handle(self, message: str) -> AgentResponse:
        resume = self._extract_resume(message)
        job_title = self._extract_job_title(message)
        jd = self._extract_jd(message)
        if not resume:
            return AgentResponse(self.name, False, "No resume text found in the message.")
        job_id = self._extract_job_id(message)
        if job_id and not repo.get_job(job_id):
            log.warning("ResumeAgent: job_id %s not found; ignoring for FK safety.", job_id)
            job_id = None
        result = self.service.adapt_for_job(resume, job_title or "the target role",
                                            jd or "", job_id=job_id)
        return AgentResponse(
            self.name, True,
            f"Resume rewritten for '{job_title}'. {len(result.change_log)} changes "
            f"logged, awaiting approval.",
            {"resume_id": result.resume_id, "change_log": result.change_log})

    @staticmethod
    def _extract_resume(msg: str) -> str:
        m = re.search(r"\[RESUME\](.*?)\[/RESUME\]", msg, re.S)
        return m.group(1).strip() if m else ""

    @staticmethod
    def _extract_job_title(msg: str) -> str:
        m = re.search(r"job_title=['\"]([^'\"]+)", msg)
        return m.group(1) if m else ""

    @staticmethod
    def _extract_jd(msg: str) -> str:
        m = re.search(r"\[JD\](.*?)\[/JD\]", msg, re.S)
        return m.group(1).strip() if m else ""

    @staticmethod
    def _extract_job_id(msg: str) -> str | None:
        m = re.search(r"job_id=['\"]([^'\"]+)", msg)
        return m.group(1) if m else None


# ---------------------------------------------------------------------------
# 2) Cover letter drafting agent
# ---------------------------------------------------------------------------
class CoverLetterAgent(BaseAgent):
    name = "cover_letter_draft"

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.service = CoverLetterService(user_id)

    def handle(self, message: str) -> AgentResponse:
        resume = self._extract(message, "RESUME")
        job_title = self._extract(message, "JOB_TITLE")
        company = self._extract(message, "COMPANY")
        jd = self._extract(message, "JD")
        tone = self._extract(message, "TONE") or "Formal"
        if not resume:
            return AgentResponse(self.name, False, "No resume text provided.")
        cl = self.service.generate_and_save(
            resume, job_title or "the role", company or "",
            jd or "", job_id=self._extract(message, "JOB_ID"), tone=tone)
        return AgentResponse(self.name, True,
                             f"Cover letter drafted ({tone}) for {company or job_title}.",
                             {"cover_letter_id": cl.cover_letter_id})

    @staticmethod
    def _extract(msg: str, tag: str) -> str:
        m = re.search(rf"\[{tag}\]=(.*?)(?=\n\[|\Z)", msg, re.S)
        return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# 3) Job search filtering agent
# ---------------------------------------------------------------------------
class JobSearchAgent(BaseAgent):
    name = "job_search_filter"

    def __init__(self, user_id: str):
        self.user_id = user_id

    def handle(self, message: str) -> AgentResponse:
        # Parse a simple intent: e.g. "find python jobs in US remote, salary 100-200k"
        keywords = self._kw(message)
        country = self._country(message)
        remote = "remote" in message.lower()
        filters = SearchFilters(keywords=keywords, country=country,
                                remote_only=remote)
        orchestrator = JobSearchOrchestrator(filters)
        jobs = orchestrator.run()
        return AgentResponse(self.name, True,
                             f"Found {len(jobs)} jobs. Methods: {orchestrator.methods_used}",
                             {"jobs": jobs[:10]})

    @staticmethod
    def _kw(msg: str) -> str:
        m = re.search(r"for ([a-z0-9+#. ]+?) (?:jobs|positions|roles)", msg, re.I)
        return m.group(1).strip() if m else (msg.split() or [""])[0]

    @staticmethod
    def _country(msg: str) -> str:
        for key in ("US", "UK", "Germany", "Canada", "Australia", "Singapore", "UAE"):
            if key.lower() in msg.lower():
                return key
        return "US"


# ---------------------------------------------------------------------------
# Registry (MCP-tool-style routing)
# ---------------------------------------------------------------------------
AGENT_REGISTRY = {
    "resume_rewrite": ResumeAgent,
    "cover_letter_draft": CoverLetterAgent,
    "job_search_filter": JobSearchAgent,
}
