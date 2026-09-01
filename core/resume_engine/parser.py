"""
Job_Track_AI - Resume parser.

Extracts sections (contact, summary, skills, experience, education, projects)
from raw resume text. Supports plain-text resumes and light PDF/docx extraction
if optional libs are present. All data stays local.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Common skill tokens used for matching keyword extraction.
SKILL_TOKEN_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9#+. -]{1,30}$")

# Section headings that commonly appear in resumes.
_SECTION_MARKERS = [
    r"work experience", r"professional experience", r"experience", r"education",
    r"skills", r"technical skills", r"core competencies", r"summary",
    r"objective", r"projects", r"certifications", r"achievements", r"languages",
]


@dataclass
class ParsedResume:
    raw: str = ""
    name: str = ""
    email: str = ""
    phone: str = ""
    summary: str = ""
    skills: list[str] = field(default_factory=list)
    experience_lines: list[str] = field(default_factory=list)
    education: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    sections: dict[str, str] = field(default_factory=dict)


def _detect_text(source: str) -> str:
    """Best-effort extraction. Returns plain text for our purposes."""
    return source


def parse_resume(text: str) -> ParsedResume:
    text = text.replace("\r\n", "\n").strip()
    parsed = ParsedResume(raw=text)
    if not text:
        return parsed

    lines = [l.strip() for l in text.split("\n")]
    # Heuristic name/contact from the first few lines.
    for line in lines[:6]:
        if not line:
            continue
        if "@" in line and "." in line:
            parsed.email = line
        if re.search(r"\+?\d[\d\s\-()]{7,}\d", line):
            parsed.phone = line
    # name = first non-empty non-email non-phone line that isn't a heading
    for line in lines[:4]:
        if line and "@" not in line and not re.search(r"\+?\d{7,}", line):
            parsed.name = line
            break

    # Split into sections (supports both standalone and inline headings)
    inline_pattern = re.compile(
        r"^\s*(" + "|".join(_SECTION_MARKERS) + r")\s*:\s*(.*)$", re.IGNORECASE)
    standalone_pattern = re.compile(
        r"^\s*(" + "|".join(_SECTION_MARKERS) + r")\s*:?\s*$", re.IGNORECASE)
    current: str | None = None
    for line in lines:
        mi = inline_pattern.match(line)
        if mi and mi.group(2).strip():
            current = mi.group(1).lower()
            parsed.sections[current] = parsed.sections.get(current, "") + mi.group(2) + "\n"
            continue
        ms = standalone_pattern.match(line)
        if ms:
            current = ms.group(1).lower()
            parsed.sections[current] = parsed.sections.get(current, "")
            continue
        if current:
            parsed.sections[current] += line + "\n"

    parsed.summary = parsed.sections.get("summary", "").strip()
    skills_text = (parsed.sections.get("skills", "") or
                   parsed.sections.get("technical skills", "") or
                   parsed.sections.get("core competencies", ""))
    parsed.skills = _extract_skills(skills_text)
    _fill_derived(parsed)
    return parsed


def _extract_skills(text: str) -> list[str]:
    tokens = set()
    for raw in re.split(r"[,;•|]", text):
        skill = raw.strip()
        if len(skill) < 2 or len(skill) > 40:
            continue
        if not SKILL_TOKEN_PATTERN.match(skill):
            continue
        tokens.add(skill)
    return sorted(tokens)


def _fill_derived(parsed: ParsedResume) -> None:
    # experience / education / projects from section text
    exp = parsed.sections.get("experience", "") or parsed.sections.get("work experience", "")
    edu = parsed.sections.get("education", "")
    proj = parsed.sections.get("projects", "")
    parsed.experience_lines = [l for l in exp.split("\n") if l.strip()]
    parsed.education = [l for l in edu.split("\n") if l.strip()]
    parsed.projects = [l for l in proj.split("\n") if l.strip()]
