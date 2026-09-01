# Local Rebuild & Debugging Plan — Job_Track_AI

This is your step-by-step plan to rebuild from source and debug on your own
machine. Everything runs locally; no external account is required for the core.

## Prerequisites (Windows)
- **Python 3.10+** (`python --version`). Install from python.org, checking "Add
  to PATH".
- **Git** (for the repo step; not strictly needed to run from a zip).
- Internet access for `pip` (or vendored wheels).

## 1. Get the code
Two ways:
- **Zip (recommended):** download `Job_Track_AI-<version>.zip` from the release
  / artifact. Extract to a folder, e.g. `C:\Job_Track_AI`.
- **Git:** `git clone https://github.com/<you>/Job_Track_AI.git`

## 2. Create a virtual environment
```powershell
cd C:\Job_Track_AI
python -m venv .venv
.venv\Scripts\activate
```

## 3. Install dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```
Optional extras (only if you want them):
```powershell
pip install selenium webdriver-manager      # JS scraping / browser submit
pip install plyer                            # rich desktop notifications
pip install speech_recognition pyttsx3 sounddevice   # voice
# GCP / Gemini / Calendar / Gmail / Twilio — install only if configuring them
```

## 4. Configure secrets
```powershell
copy .env.example .env
# edit .env: set APP_ENCRYPTION_KEY (generate: python -c "import secrets;print(secrets.token_hex(32))")
# set only the keys you use. NEVER commit .env.
```

## 5. Run the app
```powershell
python main.py            # launch the desktop GUI
```
Headless/CI smoke tests:
```powershell
python main.py cli diagnose
python main.py cli search --keywords Python --country US
```

## 6. Build the `.exe` locally
```powershell
python scripts/build_exe_local.py
# -> dist\JobTrackAI.exe
```
To sign (passes SmartScreen if you have a certificate):
```powershell
# set WIN_CERT_PATH / WIN_CERT_PASSWORD in .env
python scripts/build_exe_local.py --sign
```

## 7. Package a zip
```powershell
python scripts/package_local.py
```

## 8. Push to GitHub (your PAT)
```powershell
# set GITHUB_PAT / GITHUB_USERNAME in .env
python scripts/push_to_github.py
```

---

## Debugging plan

The app self-reports. `python main.py cli diagnose` runs health checks:

| Check | Meaning | Fix |
|---|---|---|
| `db_writable` | Can write the DB | Fix DB path / permissions / free space |
| `schema_integrity` | All tables present | Auto-repairs by re-running schema.sql |
| `config_sane` | Settings valid | Reset threshold/speed in `data/config.json` |
| `secrets_present` | Recommended secrets set | Set `APP_ENCRYPTION_KEY` in `.env` |
| `dependencies` | Required libs installed | `pip install -r requirements.txt` |

**When something breaks:**
1. Run `python main.py cli diagnose` — read the debug plan.
2. Check `data/jobtrack.db` is writable; if corrupt, delete `data/*.db*` (the app
   re-creates the schema). Note: this clears stored jobs/apps.
3. Check `logs/` for a trace; `core/self_diagnosis` records errors to the
   `system_logs` table too.
4. If a scraping/API source fails, it won't block the rest — sources fail
   independently and are logged.
5. If the DB was migrated/updated, verify the schema: `node_modules` no;
   run `python -c "from database import db; print(db.fetchone('select sqlite_version()'))"`.

**Logs:** `logs/jobtrack.log` (configured in `config/settings.py`).

## Common gotchas
- **Tkinter missing** on some minimal Pythons → reinstall Python with the tkinter
  package, or use a full installer.
- **`cryptography` install fails** → `pip install cryptography` directly; on
  Windows ensure you have `Microsoft C++ Build Tools` or use the prebuilt wheel.
- **Live scraping returns nothing** → it's OFF by default
  (`ENABLE_SCRAPING_REAL_SITES=false`). Set it true ONLY if you accept the
  Terms-of-Service risk; prefer the API paths.
- **SmartScreen blocks the exe** → run the Defender scan (see the CI workflow) /
  sign it, or unblock via "More info → Run anyway".

## Resuming after an interruption
```powershell
python scripts/continue_handoff.py     # prints the CONTINUE packet + status
```
or read `PROMPTS.md` at the repo root to restart the spec from scratch without
rewriting it.
