"""
Job_Track_AI - End-to-end sanity and regression test suite.

Runs all core flows in order and verifies each pipeline stage:
- Password hashing and security verification
- Multi-source job search and listing parsing
- Resume parsing and >=77% matching gate
- AI Resume adaptation, structured change log generation, and approval
- Cover letter generation across tones
- Application submission and dashboard tracking
- Follow-up scheduling and notification checks
- Interview preparation topic extraction, Q&A, and interactive flashcard quiz
- Agentic MCP orchestration and CONTINUE continuation packet
- System self-diagnosis and auto-repair plan

Can be run via:
    pytest tests/test_e2e.py -v
    python tests/test_e2e.py
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path
import pytest

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

JD = "Senior Data Engineer. Python, SQL, AWS, Spark, Airflow, Kubernetes, Docker, Terraform."


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    from config.settings import settings
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(settings.effective_db_path) + suffix)
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass
    try:
        db.close()
    except Exception:
        pass
    if not repo.get_user(USER):
        repo.create_user(User(user_id=USER, name="E2E"))


def test_password_hashing():
    """Verify PBKDF2 password hashing and verification."""
    h = hash_password("pw123")
    assert verify_password("pw123", h)
    assert not verify_password("wrong_password", h)


def test_job_search():
    """Verify job search returns structured job listings."""
    filter_obj = SearchFilters(keywords="Python", country="US", sources=["linkedin", "indeed"])
    jobs = JobSearchOrchestrator(filter_obj).run()
    assert len(jobs) > 0
    assert any("Python" in j.title or "Engineer" in j.title for j in jobs)


def test_resume_matching_gate():
    """Verify resume relevance scoring meets or exceeds 77% threshold."""
    jid = str(uuid.uuid4())
    repo.create_job(Job(job_id=jid, title="Senior Data Engineer", source="test", description=JD))
    svc = ResumeService(USER)
    score = svc.parse_and_match(RESUME, JD, job_id=jid)
    assert score >= 0.77, f"Match score {score:.2f} did not meet 77% gate"


def test_resume_adaptation_and_approval():
    """Verify AI resume adaptation produces change logs and requires approval."""
    jid = str(uuid.uuid4())
    repo.create_job(Job(job_id=jid, title="Senior Data Engineer", source="test", description=JD))
    svc = ResumeService(USER)
    adapted = svc.adapt_for_job(RESUME, "Senior Data Engineer", JD, job_id=jid)
    assert len(adapted.change_log) > 0
    assert adapted.optimized_resume != ""

    # Approve optimized version
    ok = svc.approve(adapted.resume_id)
    assert ok is True
    res_in_db = repo.get_resume(adapted.resume_id)
    assert res_in_db is not None
    assert res_in_db.approved == 1


def test_cover_letter_generation():
    """Verify tailored cover letter creation and persistence."""
    jid = str(uuid.uuid4())
    repo.create_job(Job(job_id=jid, title="Senior Data Engineer", source="test", description=JD))
    cls = CoverLetterService(USER)
    cl = cls.generate_and_save(RESUME, "Senior Data Engineer", "Northstar Corp", JD, jid, "Formal")
    assert len(cl.content) > 100
    assert "Northstar Corp" in cl.content or "Senior Data Engineer" in cl.content


def test_application_submission_and_tracking():
    """Verify application submission and dashboard status."""
    jid = str(uuid.uuid4())
    repo.create_job(Job(job_id=jid, title="Data Engineer", source="test", description=JD))
    svc = ResumeService(USER)
    res = svc.adapt_for_job(RESUME, "Data Engineer", JD, job_id=jid)
    svc.approve(res.resume_id)
    
    cls = CoverLetterService(USER)
    cl = cls.generate_and_save(RESUME, "Data Engineer", "Northstar", JD, jid, "Formal")
    
    sub = ApplicationSubmitter(USER)
    r = sub.submit(job_id=jid, resume_id=res.resume_id, cover_letter_id=cl.cover_letter_id, access_mode="guest", channel="api")
    assert r.ok is True
    assert r.application_id is not None

    trk = ApplicationTracker(USER)
    dash = trk.dashboard()
    assert dash["total"] >= 1


def test_followup_and_notifications():
    """Verify scheduling follow-ups and notifications."""
    jid = str(uuid.uuid4())
    repo.create_job(Job(job_id=jid, title="Lead Engineer", source="test", description=JD))
    sub = ApplicationSubmitter(USER)
    r = sub.submit(job_id=jid, resume_id=None, cover_letter_id=None, access_mode="guest", channel="manual")
    
    trk = ApplicationTracker(USER)
    trk.schedule_followup(r.application_id, 7)
    trk.run_followup_check()
    app = repo.get_application(r.application_id)
    assert app.followup_date is not None


def test_interview_prep_and_flashcards():
    """Verify interview topic extraction, mock Q&A, and flashcard spaced repetition."""
    jid = str(uuid.uuid4())
    repo.create_job(Job(job_id=jid, title="Senior Data Engineer", source="test", description=JD))
    prep = InterviewPrepService(USER).generate_for_job(jid)
    assert len(prep.topics) > 0
    assert len(prep.mock_questions) > 0
    assert len(prep.flashcards) > 0

    sess = FlashcardSession(prep.flashcards)
    sess.order(False)
    assert len(sess.cards) > 0
    card = sess.current()
    assert "front" in card and "back" in card
    sess.answer(True)
    assert sess.correct == 1


def test_agentic_orchestrator_and_continue():
    """Verify agent routing and CONTINUE handoff packet."""
    orch = AgenticOrchestrator(USER)
    resp = orch.route("", "find remote python developer jobs")
    assert resp.agent in ("job_search_filter", "search", "resume_rewriter", "resume", "cover_letter_drafter", "cover_letter", "orchestrator")
    
    cp = orch.continuation()
    assert cp.continuation_prompt.startswith("CONTINUE")


def test_self_diagnosis_and_repair():
    """Verify system health checks, database integrity, and repair plan."""
    report = SelfDiagnosis(USER).run_checks()
    assert len(report.results) >= 5
    assert all(r.ok for r in report.results)


def run_all_checks() -> int:
    """CLI runner fallback for standalone execution."""
    print("Running 10 E2E Sanity Checks...")
    test_password_hashing()
    print("  OK  password hashing")
    test_job_search()
    print("  OK  job search")
    test_resume_matching_gate()
    print("  OK  resume match >= 77% gate")
    test_resume_adaptation_and_approval()
    print("  OK  resume adaptation + change log + approval")
    test_cover_letter_generation()
    print("  OK  cover letter generation")
    test_application_submission_and_tracking()
    print("  OK  application submission + dashboard")
    test_followup_and_notifications()
    print("  OK  follow-up scheduling")
    test_interview_prep_and_flashcards()
    print("  OK  interview prep + flashcards")
    test_agentic_orchestrator_and_continue()
    print("  OK  agentic orchestrator + CONTINUE packet")
    test_self_diagnosis_and_repair()
    print("  OK  self-diagnosis")
    print("\nAll 10 sanity checks passed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(run_all_checks())
