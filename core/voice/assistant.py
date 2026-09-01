"""
Job_Track_AI - Optional Jarvis-like voice assistant.

Wraps speech recognition (listen) + text-to-speech (speak) behind a clean
interface so the core logic is fully testable without audio hardware. Voice
dependencies (speech_recognition, pyttsx3) are OPTIONAL; the assistant degrades
gracefully to text-only when they are absent.

Commands are routed to the AgenticOrchestrator, so voice triggers the same
MCP-style agents (resume rewrite, cover letter, job search).
"""
from __future__ import annotations

import logging

from config.settings import settings
from core.agentic.orchestrator import AgenticOrchestrator
from core.agentic.agents import AgentResponse

log = logging.getLogger(__name__)


class VoiceAssistant:
    def __init__(self, user_id: str, wake_word: str = "jarvis"):
        self.user_id = user_id
        self.wake_word = wake_word.lower()
        self.agentic = AgenticOrchestrator(user_id)
        self._sr = None
        self._tts = None

    # -- capability detection --------------------------------------------------
    @property
    def stt_available(self) -> bool:
        if self._sr is None:
            try:
                import speech_recognition  # type: ignore
                self._sr = speech_recognition.Recognizer()
            except Exception:
                self._sr = False
        return bool(self._sr)

    @property
    def tts_available(self) -> bool:
        if self._tts is None:
            try:
                import pyttsx3  # type: ignore
                self._tts = True
            except Exception:
                self._tts = False
        return bool(self._tts)

    # -- text-to-speech -------------------------------------------------------
    def speak(self, text: str) -> None:
        if not self.tts_available:
            log.info("VOICE: %s", text)
            return
        try:
            import pyttsx3  # type: ignore
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception as exc:
            log.warning("TTS failed: %s", exc)

    # -- speech-to-text -------------------------------------------------------
    def listen(self) -> str | None:
        """Capture one utterance and return its text, or None on failure."""
        if not self.stt_available:
            return None
        try:
            import speech_recognition as sr  # type: ignore
            with sr.Microphone() as source:
                self._sr.adjust_for_ambient_noise(source)
                audio = self._sr.listen(source, timeout=6, phrase_time_limit=12)
            return self._sr.recognize_google(audio)
        except Exception as exc:
            log.info("Listen failed: %s", exc)
            return None

    # -- end-to-end command handling -----------------------------------------
    def handle_voice_command(self, transcript: str) -> AgentResponse:
        """Interpret a spoken command and route it to an agent."""
        low = transcript.lower()
        answer = "I did not understand. Try: rewrite my resume, draft a cover letter, or search for jobs."

        if self.wake_word in low:
            low = low.replace(self.wake_word, "").strip()

        intent: str | None = None
        if "resume" in low:
            intent = "resume_rewrite"
        elif "cover letter" in low or "cover letter" in low:
            intent = "cover_letter_draft"
        elif "job" in low or "search" in low or "find" in low:
            intent = "job_search_filter"

        if not intent:
            return AgentResponse("voice", False, answer)

        # Voice carries no resume/JD payload; query the stored base resume & jobs.
        resp = self._command_with_defaults(intent, low)
        self.speak(resp.message)
        return resp

    def _command_with_defaults(self, intent: str, low: str) -> AgentResponse:
        from database import repository as repo
        if intent == "job_search_filter":
            message = f"find {low.replace('jobs', '').strip() or 'software'} jobs in US"
            return self.agentic.route(intent, message)
        # resume / cover letter: use the latest stored resume if present.
        resumes = repo.list_resumes(self.user_id)
        if not resumes:
            return AgentResponse("voice", False,
                                 "No resume on file yet. Add your resume in the app first.")
        resume_text = resumes[-1].base_resume or resumes[-1].optimized_resume
        return self.agentic.route(intent, f"[RESUME]{resume_text}[/RESUME]\n"
                                          f"job_title='the target role'")
