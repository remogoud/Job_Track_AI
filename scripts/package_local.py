"""
Job_Track_AI - Package the project as a downloadable zipped folder.

Creates `<project_root>/dist/Job_Track_AI-<version>.zip` containing the source
(no .git, no secrets, no build artifacts, no DB data). Use this to keep a local
bootable copy always available, per the deliverable requirements.

Usage:  python scripts/package_local.py [--version v1.0.0]
"""
from __future__ import annotations

import zipfile
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERSION = "v1.0.0"

EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", "build", "dist",
                "data", "logs", ".mypy_cache", ".pytest_cache"}
EXCLUDE_FILES = {".env", ".env.*", "*.pyc", "*.sqlite", "*.db", "*.sqlite3", "*.log"}
# Allowlist of top-level items to include.
ALLOW_DIRS = {"config", "core", "database", "security", "gui", "scripts", "docs",
              ".github", "assets", "tests"}
ALLOW_FILES = {"main.py", "requirements.txt", ".gitignore", ".env.example",
               "PROMPTS.md", "README.md", "LICENSE", "ANTIGRAVITY_PROMPT.md"}


def main() -> int:
    version = VERSION
    if "--version" in sys.argv:
        version = sys.argv[sys.argv.index("--version") + 1]
    out_dir = PROJECT_ROOT / "dist"
    out_dir.mkdir(exist_ok=True)
    out_zip = out_dir / f"Job_Track_AI-{version}.zip"

    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in sorted(PROJECT_ROOT.iterdir()):
            if item.is_dir():
                if item.name in EXCLUDE_DIRS:
                    continue
                if item.name not in ALLOW_DIRS:
                    continue
                for file in item.rglob("*"):
                    if any(part in EXCLUDE_DIRS for part in file.parts):
                        continue
                    if file.is_file() and not _is_excluded(file):
                        zf.write(file, file.relative_to(PROJECT_ROOT))
            elif item.is_file():
                if item.name in ALLOW_FILES and not _is_excluded(item):
                    zf.write(item, item.name)

    print("Packaged:", out_zip)
    print(f"Size: {out_zip.stat().st_size / 1_000_000:.2f} MB")
    return 0


def _is_excluded(path: Path) -> bool:
    if path.name == ".env" or path.name.startswith(".env."):
        return True
    if path.suffix in (".pyc", ".sqlite", ".sqlite3", ".db", ".log", ".sqlite3-journal"):
        return True
    return False


if __name__ == "__main__":
    sys.exit(main())
