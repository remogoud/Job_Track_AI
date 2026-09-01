"""
Job_Track_AI - Agentic orchestrator + CONTINUE protocol.

Routes natural-language requests to the MCP-style agents, and implements the
`CONTINUE` handoff protocol:

  * If a build is interrupted (session ended / quota exhausted), calling
    `CONTINUE` returns a `ContinuationPacket` containing a full summary of the
    work already done, the current milestone, and the exact continuation prompt
    to paste into a fresh Arena AI account so development resumes seamlessly.

See also scripts/continue_handoff.py and docs/CONTINUATION.md.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from core.agentic.agents import AGENT_REGISTRY, AgentResponse, BaseAgent

log = logging.getLogger(__name__)


@dataclass
class ContinuationPacket:
    summary: str
    milestone: str
    completed_modules: list[str]
    next_steps: list[str]
    continuation_prompt: str
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__


class AgenticOrchestrator:
    """Routes commands to agents and tracks the pipeline state."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._agents: dict[str, BaseAgent] = {}

    def agent(self, name: str) -> BaseAgent:
        if name not in self._agents:
            cls = AGENT_REGISTRY[name]
            self._agents[name] = cls(self.user_id)
        return self._agents[name]

    def route(self, intent: str, message: str) -> AgentResponse:
        """Map an intent keyword to the correct agent."""
        intent = intent.lower().strip()
        mapping = {
            "resume": "resume_rewrite",
            "rewrite_resume": "resume_rewrite",
            "cover_letter": "cover_letter_draft",
            "draft_cover_letter": "cover_letter_draft",
            "search": "job_search_filter",
            "find_jobs": "job_search_filter",
        }
        agent_name = mapping.get(intent) or self._infer(message)
        if not agent_name:
            return AgentResponse("orchestrator", False,
                                 f"Could not infer an agent for intent '{intent}'.")
        return self.agent(agent_name).handle(message)

    @staticmethod
    def _infer(message: str) -> str | None:
        low = message.lower()
        if "cover" in low or "letter" in low:
            return "cover_letter_draft"
        if "resume" in low:
            return "resume_rewrite"
        if "job" in low or "search" in low:
            return "job_search_filter"
        return None

    # --- CONTINUE protocol --------------------------------------------------
    def continuation(self, summary_data: dict[str, Any] | None = None) -> ContinuationPacket:
        summary_data = summary_data or default_build_summary()
        return ContinuationPacket(
            summary=summary_data.get("summary", ""),
            milestone=summary_data.get("milestone", ""),
            completed_modules=summary_data.get("completed_modules", []),
            next_steps=summary_data.get("next_steps", []),
            continuation_prompt=summary_data.get("continuation_prompt", ""),
        )

    def save_continuation(self) -> str:
        """Persist the status JSON to disk so another session can resume."""
        import json as _json
        from config.settings import settings
        path = settings.project_root / "data" / "continuation.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_json.dumps(default_build_summary(), indent=2), encoding="utf-8")
        return str(path)


def default_build_summary() -> dict[str, Any]:
    """Human-readable status of the whole project, used for the CONTINUE packet."""
    msg = ("Job_Track_AI: automated job search, application tracking, resume/cover letter "
           "adaptation and interview prep desktop app.")
    return {
        "summary": msg,
        "milestone": "Core modules implemented and unit-tested on the dev branch.",
        "completed_modules": [
            "Config + secrets (.env / Windows Credential Manager)",
            "Hybrid DB layer (SQLite schema + repository + optional Cloud Sync)",
            "Job search: API-first clients + human-like navigation scrapers + orchestrator",
            "Resume engine: parsing, 77% matching, AI adaptation w/ change log + approval",
            "Cover letter generation (Formal/Enthusiastic/Concise) + follow-up automation",
            "Application submission + tracking dashboard + calendar sync + notifications",
            "Interview prep: topics, key points, mock Q&A, flashcards/quiz",
            "Agentic/MCP agents + CONTINUE protocol",
            "Self-diagnosis (in progress)",
            "Voice assistant (pending)",
            "GUI (pending)",
            "CI/CD .exe builds (pending)",
            "PROMPTS.md + docs (pending)",
        ],
        "next_steps": [
            "Build self-diagnosis module",
            "Build optional voice assistant module",
            "Build the Tkinter desktop GUI",
            "Add CI/CD GitHub Actions .exe build + local PyInstaller script",
            "Write PROMPTS.md, README, docs, debug plan and push scripts",
            "Create feature/* branches, merge to dev, tag v1.0.0",
        ],
        "continuation_prompt": (
            "CONTINUE\n\nContinuing Job_Track_AI. The repo already has working core "
            "modules (see data/continuation.json). Please resume by building the "
            "remaining modules in order: self-diagnosis, voice assistant, desktop GUI, "
            "CI/CD .exe builds, then documentation and PROMPTS.md. Reuse the existing "
            "architecture: config/settings.py, database/ (SQLite hybrid), core/* "
            "services, security/ secret-only access, and the feature-branch git "
            "convention. Nothing should be re-written from scratch."
        ),
    }
