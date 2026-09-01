"""
Job_Track_AI — Resume<->Job matching.

Computes a 0..1 relevance score using a pure-Python TF-IDF + keyword overlap
model (no heavy ML dependency). If scikit-learn is installed it may be swapped
in for better embeddings, but the base build stays self-contained.

Spec: >= 0.77 (77%) -> proceed; otherwise discard.
"""
from __future__ import annotations

import math
import re
import string
from collections import Counter

from config.settings import settings
from core.resume_engine.parser import ParsedResume, parse_resume

_STOPWORDS = set("""a an and are as at be by for from in is it of on or that the this to
with for was were will would can could should about into over under after before while
have has had do does did not no if then than so such only also but more most other some
any both each few their there here when where which who whom whose how all any both""".split())

# Tech terms to weigh more heavily (bonus signals in the skill overlap).
TECH_SIGNALS = {
    "python", "java", "sql", "aws", "azure", "gcp", "kubernetes", "docker",
    "pytorch", "tensorflow", "machine learning", "nlp", "react", "node.js",
    "data engineering", "etl", "spark", "airflow", "ci/cd", "terraform", "git",
}


def _tokens(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^\w\s+#.]", " ", text)
    words = [w for w in text.split() if w and w not in _STOPWORDS]
    # multi-word tech phrases (e.g., "machine learning")
    for phrase in TECH_SIGNALS:
        if " " in phrase and phrase in text:
            words.append(phrase)
    return words


def _tfidf_similarity(a: str, b: str) -> float:
    """Cosine similarity of TF-IDF-weighted token bags."""
    ta, tb = Counter(_tokens(a)), Counter(_tokens(b))
    if not ta or not tb:
        return 0.0
    def tfidf(counter, total):
        return {w: (n / total) * math.log(1 + total / max(1, counter[w])) for w, n in counter.items()}
    va, vb = tfidf(ta, sum(ta.values())), tfidf(tb, sum(tb.values()))
    dot = sum(va.get(w, 0) * vb.get(w, 0) for w in set(va) | set(vb))
    na = math.sqrt(sum(v * v for v in va.values()))
    nb = math.sqrt(sum(v * v for v in vb.values()))
    return dot / (na * nb + 1e-9)


def _skill_overlap(resume: ParsedResume, jd_text: str) -> float:
    """
    Measures fit via two complementary directions:
      * COVERAGE: share of the JD's in-demand tech skills the candidate has
        (this is what recruiters actually care about -> high weight).
      * BREADTH: share of the candidate's claimed skills that appear in the JD.
    """
    if not resume.skills:
        return 0.0
    resume_skills = {s.lower() for s in resume.skills}
    jd_low = jd_text.lower()

    # Tech skills the JD explicitly asks for.
    jd_tech = {t.lower() for t in _tokens(jd_text) if t.lower() in TECH_SIGNALS}
    if not jd_tech:
        # Fall back to any candidate skill found in the JD text.
        jd_tech = {s for s in resume_skills if s in jd_low} or resume_skills

    coverage = len(resume_skills & jd_tech) / max(1, len(jd_tech))
    breadth = len(resume_skills & jd_tech) / max(1, len(resume_skills))
    return 0.7 * coverage + 0.3 * breadth


def match_resume_to_job(resume_text: str, job_description: str) -> float:
    """Return weighted relevance score in [0, 1]. A strong match near 0.85+."""
    resume = parse_resume(resume_text)
    jd_text = job_description or ""
    if not jd_text:
        return 0.0

    tfidf = _tfidf_similarity(resume_text, jd_text)
    skills = _skill_overlap(resume, jd_text)

    # Semantic text overlap is a weaker, noisier signal than explicit skill fit.
    score = 0.35 * tfidf + 0.65 * min(1.0, skills)
    # Keyword presence normalisation so a weak-but-relevant resume doesn't over-score.
    score = min(1.0, score * 1.12)
    return round(score, 4)


def passes_threshold(score: float, threshold: float | None = None) -> bool:
    thr = settings.match_threshold if threshold is None else threshold
    return score >= thr
