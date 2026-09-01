"""
Job_Track_AI - Desktop GUI (Tkinter, stdlib).

A tabbed desktop app exposing the whole pipeline: job search, resume
(parse/match/adapt/approve), cover letters, application tracker/dashboard,
interview prep (flashcards), agentic assistant, voice toggle, and settings.
Runs its own worker threads so long operations do not freeze the UI.

Styled with the Nexacore Dark Theme, Vapour particle banner, and custom widgets.
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

from gui.theme import apply_theme, COLORS, FONTS
from gui.vapour import VapourHeading
from gui.widgets import ScrolledText, Card, NeoButton

log = logging.getLogger(__name__)


class JobTrackApp(tk.Tk):
    def __init__(self, user_id: str = "local-user"):
        super().__init__()
        self.title("Job_Track_AI - Automated Job Search & Tracking")
        self.geometry("1120x760")
        self.minsize(960, 640)
        self.user_id = user_id
        self._ensure_user()

        # Apply dark Nexacore design system
        apply_theme(self)

        self.progress_var = tk.StringVar(value="Ready.")
        self._build()

    def _ensure_user(self) -> None:
        from database.models import User
        if not repo.get_user(self.user_id):
            repo.create_user(User(user_id=self.user_id, name="Local User"))

    def _build(self) -> None:
        # Top Vapour Particle Banner
        self.header_banner = VapourHeading(self, title="JOB_TRACK_AI", subtitle="Automated Career Engine")
        self.header_banner.pack(fill="x", side="top")
        self.header_banner.start()

        # Notebook tabs
        self.notebook = ttk.Notebook(self)

        self.tab_search = ttk.Frame(self.notebook, style="TFrame")
        self.tab_resume = ttk.Frame(self.notebook, style="TFrame")
        self.tab_letters = ttk.Frame(self.notebook, style="TFrame")
        self.tab_track = ttk.Frame(self.notebook, style="TFrame")
        self.tab_prep = ttk.Frame(self.notebook, style="TFrame")
        self.tab_agent = ttk.Frame(self.notebook, style="TFrame")
        self.tab_settings = ttk.Frame(self.notebook, style="TFrame")

        self.notebook.add(self.tab_search, text=" Job Search ")
        self.notebook.add(self.tab_resume, text=" Resume Engine ")
        self.notebook.add(self.tab_letters, text=" Cover Letters ")
        self.notebook.add(self.tab_track, text=" Tracker ")
        self.notebook.add(self.tab_prep, text=" Interview Prep ")
        self.notebook.add(self.tab_agent, text=" AI Assistant ")
        self.notebook.add(self.tab_settings, text=" Settings ")

        # Build each tab
        self._build_search()
        self._build_resume()
        self._build_letters()
        self._build_tracker()
        self._build_prep()
        self._build_agent()
        self._build_settings()

        self.notebook.pack(fill="both", expand=True, padx=8, pady=6)

        # Status Bar
        status_bar = ttk.Frame(self, style="Dark.TFrame")
        status_bar.pack(fill="x", side="bottom", padx=8, pady=4)
        
        status_label = ttk.Label(status_bar, textvariable=self.progress_var, style="Muted.TLabel")
        status_label.pack(side="left", padx=4)
        
        mode_label = ttk.Label(status_bar, text="Nexacore Dark | Offline First", style="Muted.TLabel")
        mode_label.pack(side="right", padx=4)

    # ---- Thread Helpers --------------------------------------------------
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

    # ---- 1. SEARCH TAB ----------------------------------------------------
    def _build_search(self):
        f = self.tab_search
        
        card = Card(f)
        card.pack(fill="x", padx=10, pady=8)

        ttk.Label(card, text="Keywords", font=FONTS["body_bold"]).pack(side="left", padx=(4, 6))
        self.search_kw = ttk.Entry(card, width=28)
        self.search_kw.pack(side="left", padx=6)
        self.search_kw.insert(0, "Python Developer")

        ttk.Label(card, text="Country", font=FONTS["body_bold"]).pack(side="left", padx=(12, 6))
        self.search_country = ttk.Combobox(
            card,
            values=["US", "UK", "Germany", "Canada", "Australia", "Singapore", "UAE", "India", "Remote"],
            width=12,
            state="readonly"
        )
        self.search_country.set("US")
        self.search_country.pack(side="left", padx=6)

        self.remote_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text="Remote Only", variable=self.remote_var).pack(side="left", padx=10)

        search_btn = NeoButton(
            card,
            text="Search Jobs",
            command=self._do_search,
            width=110,
            height=30,
            bg_color=COLORS["accent_cyan"],
            hover_color=COLORS["accent_cyan_hover"],
            text_color=COLORS["bg_dark"]
        )
        search_btn.pack(side="right", padx=6)

        self.search_out = ScrolledText(f, "Search Results & Discovered Listings", height=20)
        self.search_out.pack(fill="both", expand=True, padx=10, pady=(0, 8))

    def _do_search(self):
        filters = SearchFilters(
            keywords=self.search_kw.get().strip() or "Software",
            country=self.search_country.get() or "US",
            remote_only=self.remote_var.get(),
            sources=["linkedin", "indeed", "generic"]
        )
        self.search_out.set("Searching job portals and API endpoints...")
        self.progress_var.set("Searching jobs in progress...")
        self._run_bg(lambda: JobSearchOrchestrator(filters).run(), self._on_search_done)

    def _on_search_done(self, jobs):
        if not jobs:
            self.search_out.set("No results returned. (Live scraping is OFF by default for safety; "
                                "enable it in .env or configure API keys.)")
            self.progress_var.set("Search complete. 0 results.")
            return
        lines = []
        for i, j in enumerate(jobs[:50], 1):
            lines.append(f"[{i:02d}] {j.title}\n     Company: {j.company} | Location: {j.location} | Source: {j.source}\n     Description: {j.description[:100]}...\n")
        self.search_out.set(f"Found {len(jobs)} jobs:\n\n" + "\n".join(lines))
        self.progress_var.set(f"Search complete. {len(jobs)} jobs indexed in database.")

    # ---- 2. RESUME TAB ----------------------------------------------------
    def _build_resume(self):
        f = self.tab_resume
        self.resume_in = ScrolledText(f, "Your Resume (Paste text below or load from profile)", height=8)
        self.resume_in.pack(fill="x", padx=10, pady=6)
        self.resume_in.set(BaseResume())

        act_card = Card(f)
        act_card.pack(fill="x", padx=10, pady=4)

        parse_btn = NeoButton(
            act_card,
            text="Parse & Match (>=77%)",
            command=self._parse_match,
            width=170,
            height=30,
            bg_color=COLORS["accent_blue"],
            hover_color="#60A5FA",
            text_color="#FFFFFF"
        )
        parse_btn.pack(side="left", padx=4)

        adapt_btn = NeoButton(
            act_card,
            text="Adapt for Target Role",
            command=self._adapt_resume,
            width=160,
            height=30,
            bg_color=COLORS["accent_violet"],
            hover_color=COLORS["accent_violet_hover"],
            text_color="#FFFFFF"
        )
        adapt_btn.pack(side="left", padx=4)

        approve_btn = NeoButton(
            act_card,
            text="Approve Optimized Resume",
            command=self._approve_resume,
            width=180,
            height=30,
            bg_color=COLORS["success"],
            hover_color="#34D399",
            text_color="#FFFFFF"
        )
        approve_btn.pack(side="left", padx=4)

        self.resume_out = ScrolledText(f, "Optimized Resume & AI Change Log", height=14)
        self.resume_out.pack(fill="both", expand=True, padx=10, pady=6)
        self._last_resume_id = None

    def _parse_match(self):
        text = self.resume_in.get()
        jd = getattr(self, "_last_jd", "") or "Python SQL AWS Data Engineering Microservices"
        score = ResumeService(self.user_id).parse_and_match(text, jd)
        decision = "PROCEED (>= 77% Relevance Gate Passed)" if score >= settings.match_threshold else "DISCARD (< 77% Relevance Threshold)"
        self.resume_out.set(
            f"=== RESUME MATCH ANALYSIS ===\n"
            f"Calculated Match Score: {score:.2%}\n"
            f"Gate Threshold:         {settings.match_threshold:.0%}\n"
            f"Evaluation Decision:    {decision}\n\n"
            f"Target JD Keywords: {jd}"
        )
        self.progress_var.set(f"Resume matching complete: {score:.1%} match.")

    def _adapt_resume(self):
        text = self.resume_in.get()
        job_title = "Senior Python Developer"
        jd = getattr(self, "_last_jd", "") or "Python SQL AWS Kubernetes Docker Microservices"
        self.progress_var.set("Adapting resume for target role...")
        self._run_bg(lambda: ResumeService(self.user_id).adapt_for_job(
            text, job_title, jd), self._on_adapted)

    def _on_adapted(self, resume):
        self._last_resume_id = resume.resume_id
        loglines = "\n".join(f"  * [{c.get('section', 'General')}] {c.get('action', 'update')}: {c.get('reason', 'optimization')}"
                             for c in (resume.change_log or []))
        self.resume_out.set(
            f"=== OPTIMIZED RESUME (Pending Approval) ===\n\n"
            f"{resume.optimized_resume}\n\n"
            f"=== STRUCTURED CHANGE LOG ===\n"
            f"{loglines if loglines else '  * No major section edits required.'}\n\n"
            f"[Click 'Approve Optimized Resume' to finalize this version for submissions]"
        )
        self.progress_var.set("Resume adapted. Waiting for user approval.")

    def _approve_resume(self):
        if self._last_resume_id and ResumeService(self.user_id).approve(self._last_resume_id):
            messagebox.showinfo("Approved", "Optimized resume approved and saved to database.")
            self.progress_var.set("Optimized resume approved.")
        else:
            messagebox.showwarning("Approval Required", "Please adapt a resume before approving.")

    # ---- 3. COVER LETTER TAB ----------------------------------------------
    def _build_letters(self):
        f = self.tab_letters
        top = Card(f)
        top.pack(fill="x", padx=10, pady=6)

        ttk.Label(top, text="Company", font=FONTS["body_bold"]).pack(side="left", padx=4)
        self.cl_company = ttk.Entry(top, width=22)
        self.cl_company.insert(0, "Acme Cloud Corp")
        self.cl_company.pack(side="left", padx=6)

        ttk.Label(top, text="Tone", font=FONTS["body_bold"]).pack(side="left", padx=(10, 4))
        self.cl_tone = ttk.Combobox(top, values=["Formal", "Enthusiastic", "Concise"],
                                    width=14, state="readonly")
        self.cl_tone.set("Formal")
        self.cl_tone.pack(side="left", padx=6)

        gen_btn = NeoButton(
            top,
            text="Generate Letter",
            command=self._generate_letter,
            width=130,
            height=30,
            bg_color=COLORS["accent_cyan"],
            hover_color=COLORS["accent_cyan_hover"],
            text_color=COLORS["bg_dark"]
        )
        gen_btn.pack(side="right", padx=6)

        self.cl_out = ScrolledText(f, "Tailored Cover Letter & Follow-up Hook", height=20)
        self.cl_out.pack(fill="both", expand=True, padx=10, pady=(0, 6))

    def _generate_letter(self):
        resume = self.resume_in.get() or BaseResume()
        jd = getattr(self, "_last_jd", "") or "Python SQL AWS Architecture"
        comp = self.cl_company.get().strip() or "Acme Corp"
        cl = CoverLetterService(self.user_id).generate_and_save(
            resume, "Senior Developer", comp, jd, None, tone=self.cl_tone.get())
        self.cl_out.set(cl.content)
        self.progress_var.set(f"Cover letter generated ({self.cl_tone.get()} tone).")
        messagebox.showinfo("Cover Letter", "Cover letter generated and stored. Ready for application workflow.")

    # ---- 4. TRACKER TAB ---------------------------------------------------
    def _build_tracker(self):
        f = self.tab_track
        top = Card(f)
        top.pack(fill="x", padx=10, pady=6)

        ref_btn = NeoButton(
            top,
            text="Refresh Dashboard",
            command=self._refresh_dashboard,
            width=140,
            height=30,
            bg_color=COLORS["accent_cyan"],
            hover_color=COLORS["accent_cyan_hover"],
            text_color=COLORS["bg_dark"]
        )
        ref_btn.pack(side="left", padx=4)

        chk_btn = NeoButton(
            top,
            text="Run Follow-up Check",
            command=self._check_followups,
            width=150,
            height=30,
            bg_color=COLORS["accent_violet"],
            hover_color=COLORS["accent_violet_hover"],
            text_color="#FFFFFF"
        )
        chk_btn.pack(side="left", padx=4)

        self.track_out = ScrolledText(f, "Application Dashboard & Pipeline Status", height=20)
        self.track_out.pack(fill="both", expand=True, padx=10, pady=(0, 6))

    def _refresh_dashboard(self):
        d = ApplicationTracker(self.user_id).dashboard()
        stats_str = ", ".join(f"{k}: {v}" for k, v in d.get("stats", {}).items())
        interviews = d.get("interviews", [])
        recent_apps = d.get("recent", [])
        
        recent_lines = [f"  * [{a.status.upper()}] Job ID: {a.job_id} | Applied: {a.applied_at or 'N/A'}"
                        for a in recent_apps[:20]]

        self.track_out.set(
            f"=== APPLICATION PIPELINE DASHBOARD ===\n"
            f"Total Tracked Applications: {d.get('total', 0)}\n"
            f"Status Breakdown:            {stats_str if stats_str else 'None yet'}\n"
            f"Due Follow-ups:             {d.get('due_followups', 0)}\n"
            f"Scheduled Interviews:       {len(interviews)}\n\n"
            f"=== RECENT SUBMISSIONS ===\n"
            + ("\n".join(recent_lines) if recent_lines else "  No submissions recorded yet.")
        )
        self.progress_var.set("Dashboard refreshed.")

    def _check_followups(self):
        ApplicationTracker(self.user_id).run_followup_check()
        messagebox.showinfo("Follow-up System", "Follow-up verification check completed.")
        self.progress_var.set("Follow-up notifications check complete.")

    # ---- 5. INTERVIEW PREP TAB --------------------------------------------
    def _build_prep(self):
        f = self.tab_prep
        top = Card(f)
        top.pack(fill="x", padx=10, pady=6)

        gen_btn = NeoButton(
            top,
            text="Generate Prep for Job",
            command=self._gen_prep,
            width=160,
            height=30,
            bg_color=COLORS["accent_blue"],
            hover_color="#60A5FA",
            text_color="#FFFFFF"
        )
        gen_btn.pack(side="left", padx=4)

        fc_btn = NeoButton(
            top,
            text="Start Flashcards",
            command=self._start_flashcards,
            width=130,
            height=30,
            bg_color=COLORS["accent_cyan"],
            hover_color=COLORS["accent_cyan_hover"],
            text_color=COLORS["bg_dark"]
        )
        fc_btn.pack(side="left", padx=4)

        rev_btn = NeoButton(
            top,
            text="Reveal Answer",
            command=self._reveal_card,
            width=120,
            height=30,
            bg_color=COLORS["accent_violet"],
            hover_color=COLORS["accent_violet_hover"],
            text_color="#FFFFFF"
        )
        rev_btn.pack(side="left", padx=4)

        nxt_btn = NeoButton(
            top,
            text="Next Card",
            command=self._next_card,
            width=100,
            height=30,
            bg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_main"]
        )
        nxt_btn.pack(side="left", padx=4)

        self.prep_out = ScrolledText(f, "Interview Preparation Guide & Flashcards", height=20)
        self.prep_out.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        self._session = None

    def _gen_prep(self):
        jobs = repo.list_jobs()
        if not jobs:
            messagebox.showwarning("Interview Prep", "Run a job search first to populate listings.")
            return
        prep = InterviewPrepService(self.user_id).generate_for_job(jobs[0].job_id)
        self._display_prep(prep)

    def _display_prep(self, prep):
        topics = "\n".join(f"  * {t}" for t in prep.topics)
        qa = "\n\n".join(f"Q: {q.get('q')}\nA: {q.get('a')}" for q in prep.mock_questions)
        self.prep_out.set(
            f"=== ROLE TOPICS & FOCUS AREAS ===\n{topics}\n\n"
            f"=== MOCK QUESTIONS & KEY TALKING POINTS ===\n{qa}\n\n"
            f"[Click 'Start Flashcards' to enter active recall mode with {len(prep.flashcards)} cards]"
        )
        self._session = FlashcardSession(prep.flashcards)
        self.progress_var.set("Interview prep generated.")

    def _start_flashcards(self):
        if self._session is None:
            messagebox.showwarning("Flashcards", "Please generate interview prep first.")
            return
        self._session.order()
        card = self._session.current()
        if card:
            self.prep_out.set(
                f"=== FLASHCARD [{self._session.index + 1}/{len(self._session.cards)}] ===\n\n"
                f"FRONT (QUESTION):\n{card.get('front')}\n\n"
                f"(Click 'Reveal Answer' to check your knowledge)"
            )
            self.progress_var.set(f"Flashcard {self._session.index + 1} of {len(self._session.cards)}")

    def _reveal_card(self):
        if self._session and self._session.current():
            card = self._session.current()
            self.prep_out.set(
                f"=== FLASHCARD [{self._session.index + 1}/{len(self._session.cards)}] ===\n\n"
                f"FRONT (QUESTION):\n{card.get('front')}\n\n"
                f"BACK (ANSWER):\n{card.get('back')}\n\n"
                f"(Click 'Next Card' to proceed)"
            )

    def _next_card(self):
        if self._session and self._session.current():
            self._session.answer(True)
            card = self._session.current()
            if card:
                self.prep_out.set(
                    f"=== FLASHCARD [{self._session.index + 1}/{len(self._session.cards)}] ===\n\n"
                    f"FRONT (QUESTION):\n{card.get('front')}\n\n"
                    f"(Click 'Reveal Answer' to inspect)"
                )
                self.progress_var.set(f"Flashcard {self._session.index + 1} of {len(self._session.cards)}")
            else:
                self.prep_out.set(
                    f"=== FLASHCARD QUIZ COMPLETED ===\n\n"
                    f"Final Accuracy Score: {self._session.score():.0%}\n"
                    f"Great job mastering this role's interview requirements!"
                )
                self.progress_var.set("Flashcard session complete.")

    # ---- 6. AI ASSISTANT (AGENTIC) TAB ------------------------------------
    def _build_agent(self):
        f = self.tab_agent
        self.agent_in = ScrolledText(f, "Agent Instruction (e.g. 'rewrite resume for data engineer', 'search remote python jobs')", height=5)
        self.agent_in.pack(fill="x", padx=10, pady=6)

        act = Card(f)
        act.pack(fill="x", padx=10, pady=4)

        run_btn = NeoButton(
            act,
            text="Execute Agent Flow",
            command=self._run_agent,
            width=160,
            height=30,
            bg_color=COLORS["accent_violet"],
            hover_color=COLORS["accent_violet_hover"],
            text_color="#FFFFFF"
        )
        run_btn.pack(side="left", padx=4)

        self.agent_out = ScrolledText(f, "Agent Output & Task Execution Logs", height=16)
        self.agent_out.pack(fill="both", expand=True, padx=10, pady=6)

    def _run_agent(self):
        msg = self.agent_in.get().strip()
        if not msg:
            messagebox.showwarning("Agent", "Please provide a prompt or instruction.")
            return
        self.progress_var.set("Agent executing instruction...")
        self.agent_out.set("Routing instruction to specialized agent...")
        orch = AgenticOrchestrator(self.user_id)
        resp = orch.route("", msg)
        self.agent_out.set(
            f"=== AGENT: [{resp.agent.upper()}] ===\n"
            f"Status: SUCCESS\n\n"
            f"Response:\n{resp.message}\n\n"
            f"Payload Data:\n{resp.data if resp.data else 'None'}"
        )
        self.progress_var.set(f"Agent {resp.agent} execution completed.")

    # ---- 7. SETTINGS & DIAGNOSIS TAB --------------------------------------
    def _build_settings(self):
        f = self.tab_settings
        card = Card(f)
        card.pack(fill="x", padx=10, pady=6)

        ttk.Label(card, text="Automation Speed", font=FONTS["body_bold"]).pack(side="left", padx=4)
        self.speed = ttk.Combobox(card, values=["human", "fast"], width=12, state="readonly")
        self.speed.set("human")
        self.speed.pack(side="left", padx=6)

        save_btn = NeoButton(
            card,
            text="Save Preferences",
            command=self._save_settings,
            width=140,
            height=30,
            bg_color=COLORS["accent_cyan"],
            hover_color=COLORS["accent_cyan_hover"],
            text_color=COLORS["bg_dark"]
        )
        save_btn.pack(side="left", padx=8)

        diag_btn = NeoButton(
            card,
            text="Run Self-Diagnosis",
            command=self._run_diag,
            width=160,
            height=30,
            bg_color=COLORS["accent_blue"],
            hover_color="#60A5FA",
            text_color="#FFFFFF"
        )
        diag_btn.pack(side="left", padx=8)

        self.diag_out = ScrolledText(f, "System Health, Security Audits & Auto-Repair Plan", height=18)
        self.diag_out.pack(fill="both", expand=True, padx=10, pady=(0, 6))

    def _save_settings(self):
        from config.config_manager import ConfigManager
        cm = ConfigManager()
        cm.set("automation_speed", self.speed.get(), persist=True)
        messagebox.showinfo("Settings", "Configuration saved successfully.")
        self.progress_var.set("Settings persisted.")

    def _run_diag(self):
        report = SelfDiagnosis(self.user_id).run_checks()
        lines = ["=== SYSTEM HEALTH & DIAGNOSIS REPORT ==="]
        for r in report.results:
            status_tag = "[OK]  " if r.ok else "[FAIL]"
            lines.append(f"{status_tag} {r.name}: {r.detail}")
        lines.append("\n=== AUTOMATED DEBUG & RECOVERY PLAN ===")
        for p in report.debug_plan:
            lines.append(f"  * {p}")
        self.diag_out.set("\n".join(lines))
        self.progress_var.set("Self-diagnosis finished.")


def BaseResume() -> str:
    return (
        "Jane Doe\n"
        "Email: jane.doe@example.com | Phone: +1-555-0199 | Location: Remote / US\n\n"
        "PROFESSIONAL SUMMARY\n"
        "Experienced Software Engineer specializing in Python, SQL, Cloud Architecture, AWS, and Distributed Systems.\n\n"
        "TECHNICAL SKILLS\n"
        "Languages & Frameworks: Python, SQL, FastAPI, Django, Flask, PyTorch, Docker, Kubernetes\n"
        "Cloud & Tools: AWS (Lambda, ECS, S3, RDS), GCP, Git, CI/CD, Terraform\n\n"
        "WORK EXPERIENCE\n"
        "Senior Software Engineer | Tech Solutions Inc (2021 - Present)\n"
        "- Architected high-throughput data processing microservices in Python and AWS.\n"
        "- Optimized database querying reducing latency by 45%.\n\n"
        "Software Developer | Cloud Systems LLC (2018 - 2021)\n"
        "- Built RESTful APIs and backend microservices with automated testing suites."
    )


def run(user_id: str = "local-user"):
    app = JobTrackApp(user_id)
    app.mainloop()
