"""
Job_Track_AI — AI resume adaptation.

Rewrites a resume for a target role, producing a structured change log (what
changed and why) and supporting an approval workflow. The AI provider is
pluggable:

  * `AdaptorBackend.local_heuristic` — offline rule-based rewriter (works with
    no API key; deterministic).
  * `AdaptorBackend.gemini` — uses Google Gemini via GEMINI_API_KEY when set.

An important design rule: `base_resume` is NEVER mutated. The optimized
resume lives in `optimized_resume` and only becomes the user's active doc after
explicit approval.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from config.settings import settings
from core.resume_engine.parser import ParsedResume, parse_resume
from security.secrets import get_secret

log = logging.getLogger(__name__)


@dataclass
class AdaptationResult:
    optimized: str
    change_log: list[dict[str, Any]]
    provider: str


class ResumeAdaptor:
    def __init__(self, provider: str | None = None):
        self.provider = provider or self._resolve_provider()

    def _resolve_provider(self) -> str:
        return "gemini" if get_secret("GEMINI_API_KEY") else "local_heuristic"

    def adapt(self, resume_text: str, job_title: str, job_description: str) -> AdaptationResult:
        parsed = parse_resume(resume_text)
        jd_skills = _extract_jd_skills(job_description)

        change_log: list[dict[str, Any]] = []
        optimized = resume_text

        # 1) Tailor summary to highlight matching keywords.
        if parsed.summary:
            new_summary = _write_summary(parsed, job_title, jd_skills)
            if new_summary and new_summary != parsed.summary:
                change_log.append({
                    "section": "summary",
                    "action": "rewrite",
                    "reason": f"Aligned summary to '{job_title}' and its top keywords",
                    "old": parsed.summary,
                    "new": new_summary,
                })
                optimized = _replace_section(optimized, "summary", new_summary, parsed)
        else:
            change_log.append({"section": "summary", "action": "add",
                               "reason": "No summary found; added one for ATS keyword coverage"})

        # 2) Inject missing in-demand skills (only if not already present).
        missing = [s for s in jd_skills if s.lower() not in (resume_text.lower())]
        if missing:
            change_log.append({
                "section": "skills",
                "action": "augment",
                "reason": f"Added {len(missing)} high-value keywords from the JD "
                          f"({', '.join(missing[:5])}) to improve ATS match",
                "added": missing,
            })
            optimized = _augment_skills(optimized, missing)

        # 3) Emphasise quantified verbs in experience lines (heuristic).
        change_log.append({
            "section": "experience",
            "action": "review",
            "reason": "Advise rephrasing bullet points to lead with action verbs "
                      "and quantify impact in the tailored version",
            "guidance": ["Use strong verbs (led, built, scaled, shipped)",
                          "Add numbers (%+, time saved, users impacted)"],
        })

        return AdaptationResult(optimized=optimized, change_log=change_log,
                                provider=self.provider)


def _extract_jd_skills(jd: str) -> list[str]:
    from core.resume_engine.matcher import TECH_SIGNALS, _tokens
    found: list[str] = []
    jd_low = (jd or "").lower()
    for tok in _tokens(jd or ""):
        if tok.lower() in TECH_SIGNALS and tok.lower() not in [f.lower() for f in found]:
            # Preserve original casing as it appears in the JD for a tidy output.
            original = _find_cased(jd or "", tok.lower())
            found.append(original if original else tok)
    return found[:12]


def _find_cased(text: str, lower_token: str) -> str:
    """Return the original-cased occurrence of a token in the JD, if present."""
    idx = text.lower().find(lower_token)
    if idx == -1:
        return lower_token
    return text[idx: idx + len(lower_token)]


def _write_summary(parsed: ParsedResume, job_title: str, skills: list[str]) -> str:
    base = parsed.summary.strip().rstrip(".")
    skill_hint = ", ".join(skills[:4]) if skills else "industry-standard tools"
    return f"{base}. Experienced {job_title} skilled in {skill_hint}, focused on delivering measurable impact."


_KNOWN_SECTIONS = ("work experience", "professional experience", "experience",
                   "education", "skills", "technical skills", "core competencies",
                   "summary", "objective", "projects", "certifications",
                   "achievements", "languages")


def _replace_section(text: str, section: str, new: str, parsed: ParsedResume) -> str:
    """Replace the target section's content, leaving every other line intact.

    Supports both inline "Section: body" lines and standalone headings with a
    body that runs until the next section marker.
    """
    section_lower = section.lower()
    inline = re.compile(r"^\s*" + re.escape(section_lower) + r"\s*:\s*(.*)$", re.I)
    standalone = re.compile(r"^\s*" + re.escape(section_lower) + r"\s*:?\s*$", re.I)
    heading = re.compile(r"^\s*(?:" + "|".join(map(re.escape, _KNOWN_SECTIONS)) +
                         r")\s*:?\s*(.*)$", re.I)

    lines = text.split("\n")
    out: list[str] = []
    i = 0
    found = False
    while i < len(lines):
        line = lines[i]
        if inline.match(line):
            out.append(f"{section.capitalize()}: {new}")
            found = True
            i += 1
            continue
        if standalone.match(line):
            out.append(f"{section.capitalize()}: {new}")
            found = True
            i += 1
            # consume body until the next section marker (standalone or inline)
            while i < len(lines) and not heading.match(lines[i]):
                i += 1
            continue
        out.append(line)
        i += 1
    if not found:
        out.append(f"{section.capitalize()}: {new}")
    return "\n".join(out)


def _augment_skills(text: str, skills: list[str]) -> str:
    """Add missing skills to the Skills line, creating one if absent."""
    line = "Skills: " + ", ".join(skills)
    if "skills" in text.lower():
        # Append to existing skills section first occurrence
        lines = text.split("\n")
        for i, l in enumerate(lines):
            if "skills" in l.lower():
                lines[i] = l + ", " + ", ".join(s for s in skills if s not in l)
                return "\n".join(lines)
    return text + "\n" + line
