"""
Job_Track_AI — Build the desktop .exe on YOUR Windows machine.

Usage (on Windows):
    python -m pip install -r requirements.txt
    python -m pip install pyinstaller
    python scripts/build_exe_local.py

Produces: dist\\JobTrackAI.exe

Tips to pass Windows security checks:
  * Use a Windows Defender exclusion only for the project folder if needed.
  * For a signed build, add your code-signing certificate (signtool).
  * Run an antivirus scan after building (see the GitHub Actions workflow for a
    Start-MpScan example).
"""
from __future__ import annotations

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENTRY = PROJECT_ROOT / "main.py"
APP_NAME = "JobTrackAI"


def run(cmd: list[str]) -> None:
    print(">>", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(PROJECT_ROOT))


def check_tkinter() -> None:
    try:
        import tkinter  # noqa
        print("Tkinter available:", tkinter.TkVersion)
    except Exception as exc:
        print("WARNING: Tkinter not importable in this Python:", exc)


def build() -> None:
    check_tkinter()
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    run([sys.executable, "-m", "pip", "install", "-r", str(PROJECT_ROOT / "requirements.txt")])
    run([sys.executable, "-m", "pip", "install", "pyinstaller"])

    icon = PROJECT_ROOT / "assets" / "app.ico"
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
           "--onefile", "--windowed", "--name", APP_NAME]
    if icon.exists():
        cmd += ["--icon", str(icon)]
    cmd += ["--collect-all", "tkinter", str(ENTRY)]
    run(cmd)

    exe = PROJECT_ROOT / "dist" / f"{APP_NAME}.exe"
    if exe.exists():
        print("\nBUILD OK:", exe)
        print(f"Size: {exe.stat().st_size / 1_000_000:.1f} MB")
        print("\nTo run: double-click the exe, or")
        print(f"  {exe}")
    else:
        print("Build failed: exe not found in dist/.")


def sign() -> None:
    """Optional: sign the exe with a code-signing cert to satisfy SmartScreen.
    Point CERT_PATH / CERT_PASSWORD to your certificate via .env / Credential
    Manager (never commit them)."""
    import os
    from security.secrets import get_secret
    cert = get_secret("WIN_CERT_PATH")
    pw = get_secret("WIN_CERT_PASSWORD")
    exe = PROJECT_ROOT / "dist" / f"{APP_NAME}.exe"
    if cert and exe.exists():
        run(["signtool", "sign", "/f", cert, "/p", pw or "", "/fd", "SHA256",
             "/tr", "http://timestamp.digicert.com", "/td", "SHA256", str(exe)])
        print("Signed:", exe)
    else:
        print("No code-signing certificate configured; skipping sign step.")


if __name__ == "__main__":
    build()
    if "--sign" in sys.argv:
        sign()
