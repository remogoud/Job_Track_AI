"""
Job_Track_AI — Desktop GUI (Tkinter, stdlib).

A tabbed desktop app exposing the whole pipeline: job search, resume
(parse/match/adapt/approve), cover letters, application tracker/dashboard,
interview prep (flashcards), agentic assistant, voice toggle, and settings.
Runs its own worker threads so long operations don't freeze the UI.

This is deliberately a thin shell: real logic lives in core/* services.
"""
from __future__ import annotations

import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from config.settings import settings
from database import repository as repo
from core.job_search.filters import SearchFilters
from core.job_search.orchestrator import JobSearchOrchestrator
from core.resume_engine.service import ResumeService
from core.cover_letter.service import CoverLetterService
from core.application.submitter import ApplicationSubmitter
from core.application.tracker import ApplicationTracker
from core.interview_prep.service import InterviewPrepService
from core.interview_prep.flashcards import FlashcardSession
from core.agentic.orchestrator import AgenticOrchestrator
from core.self_diagnosis.diagnostic import SelfDiagnosis

from gui.widgets import ScrolledText

log = logging.getLogger(__name__)


class JobTrackApp(tk.Tk):
    def __init__(self, user_id: str = "local-user"):
        super().__init__()
        self.title("Job_Track_AI — Automated Job Search & Tracking")
        self.geometry("1080x720")
        self.user_id = user_id
        self._ensure_user()
        self.progress_var = tk.StringVar(value="Ready.")
        self._build()

    def _ensure_user(self) -> None:
        from database.models import User
        if not repo.get_user(self.user_id):
            repo.create_user(User(user_id=self.user_id, name="Local User"))

    def _build(self) -> None:
        notebook = ttk.Notebook(self)

        self.tab_search = ttk.Frame(notebook); notebook.add(self.tab_search, text="Search")
        self.tab_resume = ttk.Frame(notebook); notebook.add(self.tab_resume, text="Resume")
        self.tab_letters = ttk.Frame(notebook); notebook.add(self.tab_letters, text="Cover Letters")
        self.tab_track = ttk.Frame(notebook); notebook.add(self.tab_track, text="Tracker")
        self.tab_prep = ttk.Frame(notebook); notebook.add(self.tab_prep, text="Interview Prep")
        self.tab_agent = ttk.Frame(notebook); notebook.add(self.tab_agent, text="AI Assistant")
        self.tab_settings = ttk.Frame(notebook); notebook.add(self.tab_settings, text="Settings")

        # Build each tab
        self._build_search()
        self._build_resume()
        self._build_letters()
        self._build_tracker()
        self._build_prep()
        self._build_agent()
        self._build_settings()

        notebook.pack(fill="both", expand=True, padx=6, pady=4)

        status = ttk.Frame(self)
        status.pack(fill="x", side="bottom", padx=6, pady=2)
        ttk.Label(status, textvariable=self.progress_var).pack(side="left")

    # ---- helpers ---------------------------------------------------------
    def _run_bg(self, fn, on_done=None):
        def work():
            try:
                result = fn()
                if on_done:
                    self.after(0, lambda: on_done(result))
            except Exception as exc:
                log.exception("Background task failed")
                self.after(0, lambda: messagebox.showerror("Error", str(exc)))
        threading.Thread(target=work, daemon=True).start()

    # ---- SEARCHTAB -------------------------------------------------------
    def _build_search(self):
        f = self.tab_search
        top = ttk.Frame(f); top.pack(fill="x", padx=8, pady=6)
        ttk.Label(top, text="Keywords").pack(side="left")
        self.search_kw = ttk.Entry(top, width=30); self.search_kw.pack(side="left", padx=6)
        self.search_kw.insert(0, "Python")
        ttk.Label(top, text="Country").pack(side="left", padx=(10, 0))
        self.search_country = ttk.Combobox(top, values=["US", "UK", "Germany", "Canada",
                                                        "Australia", "Singapore", "UAE",
                                                        "India", "Remote"], width=10)
        self.search_country.set("US"); self.search_country.pack(side="left", padx=6)
        self.remote_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="Remote only", variable=self.remote_var).pack(side="left", padx=6)
        ttk.Button(top, text="Search", command=self._do_search).pack(side="left", padx=8)

        self.search_out = ScrolledText(f, "Results", height=24)
        self.search_out.pack(fill="both", expand=True, padx=8, pady=6)

    def _do_search(self):
        filters = SearchFilters(
            keywords=self.search_kw.get().strip() or "Software",
            country=self.search_country.get() or "US",
            remote_only=self.remote_var.get(),
            sources=["linkedin", "indeed", "generic"])
        self.search_out.set("Searching...")
        self.progress_var.set("Searching jobs...")
        self._run_bg(lambda: JobSearchOrchestrator(filters).run(),
                     self._on_search_done)

    def _on_search_done(self, jobs):
        if not jobs:
            self.search_out.set("No results. (Live scraping is OFF by default; "
                                "enable it in .env or add API keys.)")
            self.progress_var.set("Search complete. 0 results.")
            return
        text = "\n".join(f"{j.title} | {j.company} | {j.location} | {j.source}"
                         for j in jobs[:50])
        self.search_out.set(f"Found {len(jobs)} jobs:\n{text}")
        self.progress_var.set(f"Search complete. {len(jobs)} jobs stored.")

    # ---- RESUME TAB -------------------------------------------------------
    def _build_resume(self):
        f = self.tab_resume
        self.resume_in = ScrolledText(f, "Your resume (paste text)", height=10)
        self.resume_in.pack(fill="x", padx=8, pady=4)
        opt = ttk.Frame(f); opt.pack(fill="x", padx=8)
        ttk.Button(opt, text="Parse & Match", command=self._parse_match).pack(side="left", padx=2)
        ttk.Button(opt, text="Adapt for Role", command=self._adapt_resume).pack(side="left", padx=2)
        ttk.Button(opt, text="Approve Optimized", command=self._approve_resume).pack(side="left", padx=2)
        self.resume_out = ScrolledText(f, "Optimized resume + change log", height=14)
        self.resume_out.pack(fill="both", expand=True, padx=8, pady=4)
        self._last_resume_id = None

    def _parse_match(self):
        text = self.resume_in.get()
        jd = getattr(self, "_last_jd", "") or "Python SQL AWS"
        score = ResumeService(self.user_id).parse_and_match(text, jd)
        decision = "PROCEED" if score >= settings.match_threshold else "DISCARD"
        self.resume_out.set(f"Match score: {score:.2%}\nThreshold: "
                            f"{settings.match_threshold:.0%}\nDecision: {decision}")

    def _adapt_resume(self):
        text = self.resume_in.get()
        job_title = "Target Role"
        jd = getattr(self, "_last_jd", "") or "Python SQL AWS Kubernetes"
        self._run_bg(lambda: ResumeService(self.user_id).adapt_for_job(
            text, job_title, jd), self._on_adapted)

    def _on_adapted(self, resume):
        self._last_resume_id = resume.resume_id
        loglines = "\n".join(f"- {c['section']}: {c['action']} ({c['reason']})"
                             for c in resume.change_log)
        self.resume_out.set(f"OPTIMIZED RESUME:\n{resume.optimized_resume}\n\nCHANGE LOG:\n{loglines}")

    def _approve_resume(self):
        if self._last_resume_id and ResumeService(self.user_id).approve(self._last_resume_id):
            messagebox.showinfo("Approved", "Optimized resume approved and saved.")
        else:
            messagebox.showwarning("Approval", "Adapt a resume first.")

    # ---- COVER LETTER TAB ------------------------------------------------
    def _build_letters(self):
        f = self.tab_letters
        top = ttk.Frame(f); top.pack(fill="x", padx=8, pady=4)
        ttk.Label(top, text="Company").pack(side="left")
        self.cl_company = ttk.Entry(top, width=20); self.cl_company.pack(side="left", padx=6)
        ttk.Label(top, text="Tone").pack(side="left", padx=(10, 0))
        self.cl_tone = ttk.Combobox(top, values=["Formal", "Enthusiastic", "Concise"],
                                    width=12); self.cl_tone.set("Formal")
        self.cl_tone.pack(side="left", padx=6)
        ttk.Button(top, text="Generate", command=self._generate_letter).pack(side="left", padx=8)
        self.cl_out = ScrolledText(f, "Generated cover letter", height=22)
        self.cl_out.pack(fill="both", expand=True, padx=8, pady=4)

    def _generate_letter(self):
        resume = self.resume_in.get() or BaseResume()
        jd = getattr(self, "_last_jd", "") or "Python SQL AWS"
        cl = CoverLetterService(self.user_id).generate_and_save(
            resume, "Target Role", self.cl_company.get().strip() or "the company",
            jd, None, tone=self.cl_tone.get())
        self.cl_out.set(cl.content)
        messagebox.showinfo("Cover Letter", "Generated. Approve from the Tracker for use.")

    # ---- TRACKER TAB ------------------------------------------------------
    def _build_tracker(self):
        f = self.tab_track
        top = ttk.Frame(f); top.pack(fill="x", padx=8, pady=4)
        ttk.Button(top, text="Refresh Dashboard", command=self._refresh_dashboard).pack(side="left")
        ttk.Button(top, text="Check Follow-ups", command=self._check_followups).pack(side="left", padx=6)
        self.track_out = ScrolledText(f, "Dashboard / Applications", height=22)
        self.track_out.pack(fill="both", expand=True, padx=8, pady=4)

    def _refresh_dashboard(self):
        d = ApplicationTracker(self.user_id).dashboard()
        self.track_out.set(
            f"Total applications: {d['total']}\n"
            f"By status: {d['stats']}\n"
            f"Due follow-ups: {d['due_followups']}\n"
            f"Upcoming interviews: {len(d['interviews'])}\n\n"
            + "\n".join(f"{a.status}: {a.job_id}" for a in d['recent'][:30]))

    def _check_followups(self):
        ApplicationTracker(self.user_id).run_followup_check()
        messagebox.showinfo("Follow-ups", "Follow-up check complete.")

    # ---- PREP TAB ----------------------------------------------------------
    def _build_prep(self):
        f = self.tab_prep
        top = ttk.Frame(f); top.pack(fill="x", padx=8, pady=4)
        ttk.Button(top, text="Generate prep for a job", command=self._gen_prep).pack(side="left")
        ttk.Button(top, text="Start Flashcards", command=self._start_flashcards).pack(side="left", padx=6)
        ttk.Button(top, text="Next Card", command=self._next_card).pack(side="left", padx=6)
        ttk.Button(top, text="Reveal / Answer", command=self._reveal_card).pack(side="left", padx=6)
        self.prep_out = ScrolledText(f, "Topics / Q&A / Flashcards", height=22)
        self.prep_out.pack(fill="both", expand=True, padx=8, pady=4)
        self._session = None

    def _gen_prep(self):
        job_ids = [j.job_id for j in repo.list_jobs()[:1]]
        if not job_ids:
            messagebox.showwarning("Prep", "Run a job search first.")
            return
        prep = InterviewPrepService(self.user_id).generate_for_job(job_ids[0])
        self._display_prep(prep)

    def _display_prep(self, prep):
        topics = "\n".join(f"- {t}" for t in prep.topics)
        qa = "\n".join(f"Q: {q['q']}\n   A: {q['a']}" for q in prep.mock_questions)
        self.prep_out.set(f"TOPICS:\n{topics}\n\nMOCK Q&A:\n{qa}")
        self._session = FlashcardSession(prep.flashcards)

    def _start_flashcards(self):
        if self._session is None:
            messagebox.showwarning("Flashcards", "Generate prep first.")
            return
        self._session.order()
        card = self._session.current()
        self.prep_out.set(f"FLASHCARD [{self._session.index + 1}/{len(self._session.cards)}]\n"
                          f"FRONT: {card['front']}")

    def _next_card(self):
        if self._session and self._session.current():
            self._session.answer(False)
            card = self._session.current()
            if card:
                self.prep_out.set(f"FLASHCARD:\nFRONT: {card['front']}")
            else:
                self.prep_out.set(f"Quiz complete! Score: {self._session.score():.0%}")

    def _reveal_card(self):
        if self._session and self._session.current():
            card = self._session.current()
            self.prep_out.set(f"FLASHCARD:\nFRONT: {card['front']}\nBACK: {card['back']}")

    # ---- AGENT TAB ---------------------------------------------------------
    def _build_agent(self):
        f = self.tab_agent
        self.agent_in = ScrolledText(f, "Command (e.g. 'rewrite resume', 'search python jobs')", height=6)
        self.agent_in.pack(fill="x", padx=8, pady=4)
        ttk.Button(f, text="Run", command=self._run_agent).pack(side="left", padx=8, pady=4)
        self.agent_out = ScrolledText(f, "Response", height=16)
        self.agent_out.pack(fill="both", expand=True, padx=8, pady=4)

    def _run_agent(self):
        msg = self.agent_in.get()
        orch = AgenticOrchestrator(self.user_id)
        resp = orch.route("", msg)
        self.agent_out.set(f"[{resp.agent}] {resp.message}\n\n{resp.data if resp.data else ''}")

    # ---- SETTINGS TAB -------------------------------------------------------
    def _build_settings(self):
        f = self.tab_settings
        top = ttk.Frame(f); top.pack(fill="x", padx=8, pady=6)
        ttk.Label(top, text="Automation speed").pack(side="left")
        self.speed = ttk.Combobox(top, values=["human", "fast"], width=10); self.speed.set("human")
        self.speed.pack(side="left", padx=6)
        ttk.Button(top, text="Save", command=self._save_settings).pack(side="left", padx=8)
        ttk.Button(top, text="Run Self-Diagnosis", command=self._run_diag).pack(side="left", padx=8)
        self.diag_out = ScrolledText(f, "Diagnosis / debug plan", height=16)
        self.diag_out.pack(fill="both", expand=True, padx=8, pady=4)

    def _save_settings(self):
        from config.config_manager import ConfigManager
        cm = ConfigManager()
        cm.set("automation_speed", self.speed.get(), persist=True)
        messagebox.showinfo("Settings", "Saved.")

    def _run_diag(self):
        report = SelfDiagnosis(self.user_id).run_checks()
        lines = [f"{'OK' if r.ok else 'FAIL'}: {r.name} {r.detail}" for r in report.results]
        lines.append("\nDebug plan:")
        lines.extend(f"- {p}" for p in report.debug_plan)
        self.diag_out.set("\n".join(lines))


def BaseResume() -> str:
    return ("Sample Resume\nJane Doe\nData Engineer with Python, SQL, AWS, Spark.\n"
            "Skills: Python, SQL, AWS")


def run(user_id: str = "local-user"):
    app = JobTrackApp(user_id)
    app.mainloop()
