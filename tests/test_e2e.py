"""
Job_Track_AI - End-to-end smoke test of the full pipeline.

Runs the headless flows in order and asserts each step. Used by the developer
and replicable in CI. Use a fresh DB to avoid FK collisions:

    python tests/test_e2e.py
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import repository as repo, db  # noqa: E402
from database.models import User, Job  # noqa: E402
from core.job_search.filters import SearchFilters  # noqa: E402
from core.job_search.orchestrator import JobSearchOrchestrator  # noqa: E402
from core.resume_engine.service import ResumeService  # noqa: E402
from core.cover_letter.service import CoverLetterService  # noqa: E402
from core.application.submitter import ApplicationSubmitter  # noqa: E402
from core.application.tracker import ApplicationTracker  # noqa: E402
from core.interview_prep.service import InterviewPrepService  # noqa: E402
from core.interview_prep.flashcards import FlashcardSession  # noqa: E402
from core.agentic.orchestrator import AgenticOrchestrator  # noqa: E402
from core.self_diagnosis.diagnostic import SelfDiagnosis  # noqa: E402
from security.password import hash_password, verify_password  # noqa: E402

USER = "e2e-user"
RESUME = """Jane Doe
Data Engineer - 6 years building ETL pipelines with Python, Spark, Airflow, AWS, SQL.
Summary: Cloud data engineer specialising in scalable data platforms.
Skills: Python, SQL, AWS, Airflow, Spark, Kubernetes, Docker, Terraform
Experience:
- Built ETL pipelines serving 40GB/day using Airflow and Spark
- Led migration to AWS Redshift, reducing query time 38%
Education: B.S. Computer Science
"""


def _reset():
    import os
    from config.settings import settings
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(settings.effective_db_path) + suffix)
        if p.exists():
            p.unlink()
    try:
        db.close()
    except Exception:
        pass


def test() -> int:
    _reset()
    ok = 0
    def check(name, cond):
        nonlocal ok
        if cond:
            ok += 1
            print(f"  OK  {name}")
        else:
            print(f"  FAIL {name}")

    # 0) password hashing
    h = hash_password("pw123")
    check("password hash roundtrip", verify_password("pw123", h) and not verify_password("x", h))

    # 1) user + job search
    if not repo.get_user(USER):
        repo.create_user(User(user_id=USER, name="E2E"))
    filter_obj = SearchFilters(keywords="Python", country="US", sources=["linkedin", "indeed"])
    jobs = JobSearchOrchestrator(filter_obj).run()
    check("job search returns jobs", len(jobs) > 0)

    # 2) resume match (>=0.77 gate)
    jd = "Senior Data Engineer. Python, SQL, AWS, Spark, Airflow, Kubernetes, Docker, Terraform."
    jid = str(uuid.uuid4())
    repo.create_job(Job(job_id=jid, title="Senior Data Engineer", source="test", description=jd))
    svc = ResumeService(USER)
    score = svc.parse_and_match(RESUME, jd, job_id=jid)
    check(f"match score {score:.2f} meets 77% gate", score >= 0.77)

    # 3) resume adaptation + approval
    adapted = svc.adapt_for_job(RESUME, "Senior Data Engineer", jd, job_id=jid)
    check("resume adapted + change log", len(adapted.change_log) > 0)
    svc.approve(adapted.resume_id)
    check("resume approved", repo.get_resume(adapted.resume_id).approved == 1)

    # 4) cover letter + follow-up
    cls = CoverLetterService(USER)
    cl = cls.generate_and_save(RESUME, "Senior Data Engineer", "Northstar", jd, jid, "Formal")
    cls.approve(cl.cover_letter_id)
    check("cover letter generated", len(cl.content) > 100)

    # 5) application submission
    sub = ApplicationSubmitter(USER)
    r = sub.submit(job_id=jid, resume_id=adapted.resume_id,
                   cover_letter_id=cl.cover_letter_id, access_mode="guest", channel="api")
    check("application submitted", r.ok and r.application_id is not None)
    trk = ApplicationTracker(USER)
    dash = trk.dashboard()
    check("dashboard reports application", dash["total"] >= 1)

    # 6) follow-up + notifications
    trk.schedule_followup(r.application_id, 7)
    trk.run_followup_check()
    check("follow-up scheduled", repo.get_application(r.application_id).followup_date is not None)

    # 7) interview prep
    prep = InterviewPrepService(USER).generate_for_job(jid)
    sess = FlashcardSession(prep.flashcards)
    sess.order(False)
    check("interview prep flashcards", len(sess.cards) > 0)
    sess.answer(True)
    check("flashcard answer recorded", sess.correct == 1)

    # 8) agentic + CONTINUE
    orch = AgenticOrchestrator(USER)
    cp = orch.continuation()
    check("CONTINUE packet has prompt", cp.continuation_prompt.startswith("CONTINUE"))

    # 9) self-diagnosis runs
    report = SelfDiagnosis(USER).run_checks()
    check("self-diagnosis executed", len(report.results) >= 5)

    print(f"\n{ok} checks passed.")
    return 0 if ok >= 10 else 1


if __name__ == "__main__":
    sys.exit(test())
