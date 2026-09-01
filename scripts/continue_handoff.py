"""
Job_Track_AI — Print the CONTINUE continuation packet.

Use this if your Arena AI session ends or your quota is exhausted. It reads the
latest build status (data/continuation.json) and prints a ready-to-paste
`CONTINUE` prompt plus a summary of completed work, so you can resume in another
Arena AI account without rewriting the spec.

Usage:  python scripts/continue_handoff.py [--out continue_prompt.txt]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATUS_FILE = PROJECT_ROOT / "data" / "continuation.json"
PROMPTS = PROJECT_ROOT / "PROMPTS.md"


def main() -> int:
    summary = {}
    if STATUS_FILE.exists():
        summary = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    else:
        summary = {
            "milestone": "Build in progress.",
            "completed_modules": [],
            "next_steps": [],
            "continuation_prompt": "CONTINUE",
        }

    lines = [
        "=" * 70,
        "JOB_TRACK_AI — CONTINUE PACKET",
        "=" * 70,
        "",
        "MILESTONE:", summary.get("milestone", ""),
        "",
        "COMPLETED:",
    ]
    lines += [f"  - {m}" for m in summary.get("completed_modules", [])]
    lines += ["", "NEXT STEPS:", ""]
    lines += [f"  - {s}" for s in summary.get("next_steps", [])]
    lines += ["", "=" * 70, "PASTE THIS INTO A NEW ARENA AI ACCOUNT:", "=" * 70, ""]
    lines.append(summary.get("continuation_prompt", "CONTINUE"))
    lines.append("")

    text = "\n".join(lines)
    if "--out" in sys.argv:
        out_path = Path(sys.argv[sys.argv.index("--out") + 1])
        out_path.write_text(text, encoding="utf-8")
        print("Written to", out_path)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
