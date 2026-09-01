"""
Job_Track_AI - Interview preparation generator.

Extracts role requirements from the job description and produces:
  * topics             - key areas to study.
  * key points         - concise talking points per topic.
  * mock Q&A           - likely interview questions with model answers.
  * flashcards         - {front, back, repeats} cards for quiz mode.

Engine is pluggable: local_heuristic (offline) or gemini (if key set).
"""
from __future__ import annotations

import logging
import re
import random
from dataclasses import dataclass, field
from typing import Any

from core.resume_engine.matcher import _tokens, TECH_SIGNALS
from core.resume_engine.adaptor import _extract_jd_skills
from core.resume_engine.parser import parse_resume
from security.secrets import get_secret

log = logging.getLogger(__name__)

# Mapping of common tech terms -> study topics.
TOPIC_MAP = {
    "python": "Python fundamentals, OOP, data structures, Pythonic idioms",
    "sql": "SQL: joins, indexing, query optimisation, window functions",
    "aws": "AWS services, architecture, IAM, compute/storage options",
    "gcp": "Google Cloud services, BigQuery, deployment, IAM",
    "kubernetes": "Kubernetes: pods, deployments, services, scaling, helm",
    "docker": "Docker: images, containers, volumes, docker-compose",
    "spark": "Apache Spark: RDDs, DataFrames, partitioning, tuning",
    "airflow": "Airflow: DAGs, schedulers, sensors, backfills",
    "machine learning": "ML lifecycle, model evaluation, bias/variance, deployment",
    "etl": "ETL/ELT design, data quality, idempotency, incremental loads",
    "ci/cd": "CI/CD pipelines, testing, git branching, release automation",
    "react": "React: components, state, hooks, performance",
    "javascript": "JavaScript: async/await, closures, event loop",
    "java": "Java: JVM, concurrency, collections, streams",
    "node.js": "Node.js: event loop, streams, error handling",
    "terraform": "Terraform: modules, state, plan/apply, providers",
}

BEHAVIORAL = [
    ("Tell me about yourself.", "Provide a 60-second summary of your trajectory, "
     "emphasising your most relevant achievements. Structure: current role -> "
     "impact -> why this role."),
    ("Describe a time you faced a difficult technical problem.",
     "Use STAR: Situation, Task, Action, Result. Pick a concrete story with a "
     "quantified outcome."),
    ("How do you handle tight deadlines?", "Acknowledge prioritisation, timeboxing, "
     "communication of trade-offs, and a real example."),
    ("Why do you want to work here?", "Link your values + skills to the company's "
     "mission and recent achievements."),
    ("Where do you see yourself in five years?", "Show ambition aligned with growth "
     "in the role; avoid sounding uncommitted."),
]

TECH_QUESTIONS = {
    "python": ("Explain how Python handles GIL and how it affects concurrency.",
               "Mention GIL limits true parallel CPU-bound threads; practical fixes "
               "are multiprocessing, threading for I/O, and async/await for I/O-bound."),
    "sql": ("How would you optimise a slow query?",
            "Index columns in WHERE/JOIN, avoid SELECT *, use covering indexes, "
            "analyse the query plan, check for full scans and cardinality."),
    "aws": ("How do you handle high availability in AWS?",
            "Multi-AZ, auto-scaling groups, load balancers, RDS replicas, and "
            "route53 health checks / failover."),
    "kubernetes": ("Describe a Kubernetes deployment strategy.",
                   "Rolling / blue-green / canary deployments, readiness vs liveness "
                   "probes, resource limits, and horizontal pod autoscaler."),
}


@dataclass
class InterviewPrepData:
    topics: list[str] = field(default_factory=list)
    key_points: list[str] = field(default_factory=list)
    mock_questions: list[dict[str, str]] = field(default_factory=list)
    flashcards: list[dict[str, Any]] = field(default_factory=list)


class InterviewPrepGenerator:
    def __init__(self, provider: str | None = None):
        self.provider = provider or ("gemini" if get_secret("GEMINI_API_KEY") else "local_heuristic")

    def generate(self, job_title: str, job_description: str, resume_text: str = "") \
            -> InterviewPrepData:
        if self.provider.lower() == "gemini":
            try:
                return self._gemini(job_title, job_description, resume_text)
            except Exception as exc:
                log.warning("Gemini prep generation failed (%s); falling back.", exc)
        return self._heuristic(job_title, job_description, resume_text)

    def _heuristic(self, job_title: str, job_description: str, resume_text: str) \
            -> InterviewPrepData:
        skills = _extract_jd_skills(job_description)
        topics: list[str] = []
        key_points: list[str] = []
        flashcards: list[dict[str, Any]] = []
        mock_q: list[dict[str, str]] = []

        # Topics from JD tech signals
        for s in skills:
            topic = TOPIC_MAP.get(s.lower())
            if topic:
                topics.append(f"{s}: {topic}")
        if not topics:
            topics.append(f"General {job_title} role overview and responsibilities")
            topics.append("Company fit, culture, and business context")

        # Key points
        resume = parse_resume(resume_text)
        for s in skills[:5]:
            key_points.append(f"Be ready to discuss hands-on examples using {s}.")
        key_points.append("Prepare 2-3 quantified achievements (numbers, %, impact).")
        key_points.append("Know the job requirements and map each to a concrete win.")

        # Technical Q&A for the top skills
        js = job_description.lower()
        for s in skills:
            qa = TECH_QUESTIONS.get(s.lower())
            if qa:
                mock_q.append({"q": qa[0], "a": qa[1]})
        # Behavioral questions
        for q, a in BEHAVIORAL[:4]:
            mock_q.append({"q": q, "a": a})

        # Flashcards
        for s in skills[:8]:
            flashcards.append({"front": f"What is your experience with {s}?",
                               "back": f"Prepare 1 concrete project + metric using {s}.",
                               "repeats": 0})
        for q, a in mock_q[:6]:
            flashcards.append({"front": q, "back": a, "repeats": 0})

        return InterviewPrepData(topics=topics, key_points=key_points,
                                 mock_questions=mock_q, flashcards=flashcards)

    def _gemini(self, job_title: str, job_description: str, resume_text: str) \
            -> InterviewPrepData:
        """Optional Gemini-backed generation. Returns structured data via JSON."""
        import json as _json
        from security.secrets import get_secret as _gs
        key = _gs("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY missing")
        # Build prompt and call Gemini generative API, parse JSON response into
        # InterviewPrepData. Wired for future use; endpoint lazy.
        raise NotImplementedError("Gemini prep wiring is a TODO - fall back to heuristic.")
