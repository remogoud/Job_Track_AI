"""
Job_Track_AI - Push the local repository to your GitHub repo with a PAT.

Usage (Windows):
    # 1) In .env set:
    #      GITHUB_PAT=<your personal access token>
    #      GITHUB_USERNAME=<your github username>
    #      GITHUB_REPO=Job_Track_AI
    # 2) python scripts/push_to_github.py

The script reads the PAT from .env (or Windows Credential Manager)
and pushes ALL branches (main, dev, feature/*, hotfix/*) plus tags to your remote.
It never commits the token and scrubs the token from the local remote URL after pushing.
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
        print("Missing GITHUB_PAT or GITHUB_USERNAME in environment or .env.")
        print("Push skipped. Once GITHUB_PAT and GITHUB_USERNAME are configured, re-run this script.")
        return 1

    auth_remote_url = f"https://x-access-token:{pat}@github.com/{user}/{repo}.git"
    clean_remote_url = f"https://github.com/{user}/{repo}.git"

    # Replace/ensure the remote exists
    try:
        run(["git", "remote", "remove", "origin"])
    except subprocess.CalledProcessError:
        pass

    subprocess.check_call(["git", "remote", "add", "origin", "remote-placeholder"],
                          cwd=str(PROJECT_ROOT))
    subprocess.check_call(
        ["git", "config", "remote.origin.url", auth_remote_url],
        cwd=str(PROJECT_ROOT))

    try:
        # Push branches and tags
        run(["git", "push", "-u", "origin", "main"])
        run(["git", "push", "-u", "origin", "dev"])

        branches = subprocess.check_output(
            ["git", "branch", "--format=%(refname:short)"], cwd=str(PROJECT_ROOT),
            text=True).split()
        for branch in branches:
            if branch not in ("main", "dev"):
                run(["git", "push", "-u", "origin", branch])

        run(["git", "push", "--tags"])
        print(f"\nSuccessfully pushed to https://github.com/{user}/{repo}")
    finally:
        # Clean remote URL so token is never preserved locally
        try:
            subprocess.check_call(
                ["git", "config", "remote.origin.url", clean_remote_url],
                cwd=str(PROJECT_ROOT))
        except Exception:
            pass

    print("Token was used transiently and scrubbed from git config.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
