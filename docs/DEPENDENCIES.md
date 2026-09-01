# External Dependencies — Job_Track_AI

The app is designed to run **fully locally** with free services. Cloud/optional
features are opt-in. Below is an explicit, honest list of every external
dependency and free alternatives.

## Runtime (required, free)
| Component | Where | Cost | Notes |
|---|---|---|---|
| Python 3.10+ | — | Free | GUI uses stdlib `tkinter` |
| SQLite | stdlib | Free | Default local store (offline control) |
| `requests`, `beautifulsoup4`, `pydantic`, `cryptography`, `python-dateutil` | pip | Free | Core; `cryptography` for AES-GCM |

## Optional / gated dependencies
| Component | Purpose | Free alternative |
|---|---|---|
| Selenium + WebDriver | JS-heavy / authenticated scraping & browser submission | Requests-based session; prefer API |
| scikit-learn | Enhanced matching (optional) | Bundled pure-Python TF-IDF matcher |
| `plyer` | Rich desktop notifications | Stdlib fallback (GUI reads queue) |
| `speech_recognition`, `pyttsx3`, `sounddevice` | Voice assistant | Text-only mode (auto-degraded) |
| `google-cloud-firestore`, `google-cloud-storage`, `google-api-python-client` | GCP sync + Gemini/Calendar/Gmail/Drive | Local SQLite + local file export |
| `google-cloud-sql` (+ `sqlalchemy`/`pg8000`) | Cloud SQL for scale | Stay on SQLite |

## External services explicitly used (only if you enable them)
| Service | Cost | Used for | Free alternative |
|---|---|---|---|
| **Google Cloud** (Firestore / Cloud SQL) | Pay-as-you-go (has free tier) | Scalability + Gemini/Calendar/Gmail/Drive | Local SQLite (already the default) |
| **Google Gemini** | Free tier available | AI resume rewrite, cover letters, prep (provider plug-in) | The **local heuristic** engine (no key needed) |
| **LinkedIn Jobs API** | Partner access (may require approval) | ToS-compliant job search | Scraping (off by default) or manual |
| **Indeed API** | Partner access | ToS-compliant job search | Scraping or manual |
| **Twilio** | Pay-as-you-go (free trial credit) | SMS follow-up notifications | Desktop notifications (default) |
| **ngrok** | Free tier | Local tunneling (only for remote dev access) | Not needed for normal use |
| **AWS** | Pay-as-you-go | Only if you prefer AWS over GCP | Not needed; hybrid SQLite/GCP built-in |

> **Preference:** the app defaults to **free / local** (SQLite, stdlib Tkinter,
> local heuristic AI). Every optional paid integration is OFF until you set its
> secrets in `.env` / Credential Manager.

## Windows Credential Manager (recommended for secrets)
`security/secrets.py` reads from Credential Manager (via `win32cred`) first.
You can store, e.g.:
- service `JobTrackAI`, key `GITHUB_PAT`
- service `JobTrackAI`, key `APP_ENCRYPTION_KEY`
- service `JobTrackAI`, key `LINKEDIN_ACCESS_TOKEN`
