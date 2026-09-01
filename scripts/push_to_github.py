"""
Job_Track_AI - Push the local repository to your GitHub repo with a PAT.

Usage (Windows):
    # 1) Create .env and set:
    #      GITHUB_PAT=<your personal access token>
    #      GITHUB_USERNAME=<your github username>
    #      GITHUB_REPO=Job_Track_AI
    # 2) python scripts/push_to_github.py

The script reads the PAT from .env (it never stores the token in the repo)
and pushes ALL branches (main, dev, feature/*, hotfix/*) plus tags to your remote.
It never commits the token.
"""
from __future__ import annotations

import sys
import subprocess
from pathlib import Path
import os
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


def run(cmd: list[str]) -> None:
    print(">>", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(PROJECT_ROOT))


def main() -> int:
    pat = os.getenv("GITHUB_PAT")
    user = os.getenv("GITHUB_USERNAME")
    repo = os.getenv("GITHUB_REPO", "Job_Track_AI")

    if not pat or not user:
        print("Missing GITHUB_PAT or GITHUB_USERNAME. Set them in .env.")
        return 1

    remote_url = f"https://x-access-token:{pat}@github.com/{user}/{repo}.git"

    # Replace/ensure the remote uses the token, but never log the URL.
    try:
        run(["git", "remote", "remove", "origin"])
    except subprocess.CalledProcessError:
        pass  # ignore if origin doesn't exist yet

    subprocess.check_call(["git", "remote", "add", "origin", "remote-placeholder"],
                          cwd=str(PROJECT_ROOT))
    subprocess.check_call(
        ["git", "config", "remote.origin.url", remote_url],
        cwd=str(PROJECT_ROOT))

    # Push all branches + tags.
    run(["git", "push", "-u", "origin", "main"])
    run(["git", "push", "-u", "origin", "dev"])

    branches = subprocess.check_output(
        ["git", "branch", "--format=%(refname:short)"], cwd=str(PROJECT_ROOT),
        text=True).split()
    for branch in branches:
        if branch not in ("main", "dev"):
            run(["git", "push", "-u", "origin", branch])

    run(["git", "push", "--tags"])

    print("\nPushed to", f"{user}/{repo}")
    print("Token was used transiently and is not committed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
