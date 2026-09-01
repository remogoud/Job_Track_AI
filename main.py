"""
Job_Track_AI - Application entry point.

Launches the desktop GUI. Also supports a headless CLI mode for scripting /
automation / CI sanity checks.
"""
from __future__ import annotations

import sys
import logging

from config.settings import settings


def _setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def run_gui() -> None:
    from gui.app import run
    run()


def run_cli(args: list[str]) -> int:
    """Minimal headless mode: `python main.py cli search --keywords Python`.
    Useful for automation and for CI smoke-tests of the pipeline."""
    if args and args[0] == "cli":
        from database import repository as repo
        from core.job_search.filters import SearchFilters, COUNTRIES
        from core.job_search.orchestrator import JobSearchOrchestrator
        cmd = args[1] if len(args) > 1 else "search"
        if cmd == "search":
            kw = args[args.index("--keywords") + 1] if "--keywords" in args else "Python"
            country = args[args.index("--country") + 1] if "--country" in args else "US"
            filters = SearchFilters(keywords=kw, country=country)
            jobs = JobSearchOrchestrator(filters).run()
            print(f"Found {len(jobs)} jobs.")
            for j in jobs[:5]:
                print(f"  {j.title} | {j.company} | {j.location} | {j.source}")
            return 0
        if cmd == "diagnose":
            from core.self_diagnosis.diagnostic import SelfDiagnosis
            report = SelfDiagnosis().run_checks()
            ok = report.healthy
            for r in report.results:
                print(f"{'OK' if r.ok else 'FAIL'}: {r.name} {r.detail}")
            return 0 if ok else 1
    print(__doc__)
    return 0


def main() -> None:
    _setup_logging()
    args = sys.argv[1:]
    if args and args[0] == "cli":
        sys.exit(run_cli(args))
    # launch GUI
    try:
        run_gui()
    except Exception as exc:
        logging.exception("GUI failed to start")
        print(f"GUI failed to start: {exc}")


if __name__ == "__main__":
    main()
