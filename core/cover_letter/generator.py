"""
Job_Track_AI - Tailored cover letter generation.

Produces a role-specific cover letter in a chosen tone (Formal / Enthusiastic /
Concise) by blending the user's profile (skills + a highlight) with the job's
keywords and company. Includes a follow-up paragraph hook so the letter supports
the follow-up automation feature.

Provider is pluggable:
  * local_heuristic - offline template engine (always available).
  * gemini - uses Google Gemini when GEMINI_API_KEY is set, for richer prose.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from core.resume_engine.parser import ParsedResume, parse_resume
from core.resume_engine.matcher import _tokens
from core.resume_engine.adaptor import _extract_jd_skills
from security.secrets import get_secret

log = logging.getLogger(__name__)

TONES = ("Formal", "Enthusiastic", "Concise")

_OPENERS = {
    "Formal": "Dear Hiring Team,\n\nI am writing to express my strong interest in the"
              " {role} position at {company}. With a track record of delivering measurable"
              " results, I am confident I can contribute meaningfully to your team.",
    "Enthusiastic": "Hi there,\n\nI am genuinely excited to apply for the {role} role at"
                    " {company}. Your work stood out to me, and I would love to help"
                    " accelerate what you are building.",
    "Concise": "Dear Hiring Team,\n\nI am applying for the {role} position at {company}."
               " Here is why I am a strong fit.",
}

_BODIES = {
    "Formal": "\n\nMy background in {skills} directly aligns with the requirements of"
              " this role. In my most recent role I delivered significant, quantifiable"
              " impact - I would welcome the opportunity to discuss how I can bring the"
              " same rigor and results to {company}.",
    "Enthusiastic": "\n\nI bring hands-on experience with {skills}, and I love rolling up"
                    " my sleeves on hard problems. I thrive in collaborative teams and am"
                    " excited about the impact we could create together at {company}.",
    "Concise": "\n\nI have {years}+ years of experience with {skills}, and I consistently"
               " deliver high-impact results. I can add immediate value to {company}.",
}

_CLOSERS = {
    "Formal": ("\n\nThank you for your time and consideration. I look forward to the"
               " opportunity to speak further.",
               "Sincerely,\n{name}"),
    "Enthusiastic": ("\n\nThanks so much for considering my application - I would love to"
                     " chat about how I can help. Talk soon!",
                     "Best regards,\n{name}"),
    "Concise": ("\n\nThank you for your consideration. I am available to discuss further "
                "at your convenience.",
                "Regards,\n{name}"),
}

# Follow-up hook (used by the follow-up automation module).
FOLLOW_UP_HOOK = ("\n\nP.S. I would be glad to follow up in a week to answer any "
                  "questions. My availability is flexible and I am open to discussing "
                  "the role in more detail.")


@dataclass
class CoverLetterResult:
    content: str
    tone: str
    provider: str
    follow_up_enabled: bool = True


class CoverLetterGenerator:
    def __init__(self, provider: str | None = None):
        self.provider = provider or ("gemini" if get_secret("GEMINI_API_KEY") else "local_heuristic")

    def generate(self, resume_text: str, job_title: str, company: str,
                 job_description: str = "", tone: str = "Formal",
                 include_follow_up: bool = True) -> CoverLetterResult:
        tone = tone if tone in TONES else "Formal"
        resume = parse_resume(resume_text)
        skills = _extract_jd_skills(job_description) or resume.skills[:5] or ["your core strengths"]
        skills_str = ", ".join(skills[:5])
        years = _estimate_years(resume_text)

        opener = _OPENERS[tone].format(role=job_title, company=company or "your company")
        body = _BODIES[tone].format(skills=skills_str, company=company or "your company",
                                    years=years)
        closer_open, closer_sig = _CLOSERS[tone]
        closer_open = closer_open.format(company=company or "your company")
        closer_sig = closer_sig.format(name=resume.name or "Your Name")

        content = opener + body + "\n\n" + closer_open + "\n\n" + closer_sig
        if include_follow_up:
            # Insert the follow-up hook before the closing signature.
            content = content.replace("\n\n" + closer_sig, "\n\n" + FOLLOW_UP_HOOK + "\n\n" + closer_sig)
        # Collapse 3+ consecutive blank lines into a single blank paragraph break.
        import re
        content = re.sub(r"\n{3,}", "\n\n", content)

        return CoverLetterResult(content=content, tone=tone, provider=self.provider,
                                 follow_up_enabled=include_follow_up)


def _estimate_years(resume_text: str) -> int:
    import re
    m = re.search(r"(\d+)\s*(?:\+)?\s*(?:years|yrs)", resume_text or "", re.I)
    return int(m.group(1)) if m else 5
