# Security & Compliance - Job_Track_AI

## Secrets handling (the "no secrets in repo" rule)

- All keys live in **`.env`** (git-ignored) or **Windows Credential Manager**.
- `security/secrets.py` reads them in this priority: Windows Credential Manager →
  environment variables → `.env`.
- `.gitignore` excludes `.env`, `*.key`, `*.pem`, `credentials.json`,
  `service_account.json`, `data/`, `*.db`, `build/`, `dist/`, `*.exe`, etc.
- The push/build scripts never log token values.
- Secrets are cached in-process and never written to logs.

### Secrets to configure (in `.env` / Credential Manager)

| Variable | Purpose | Required? |
|---|---|---|
| `APP_ENCRYPTION_KEY` | AES-256-GCM key for email encryption | Recommended (else ephemeral) |
| `GITHUB_PAT` / `GITHUB_USERNAME` | Push script only | For push only |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn Jobs API | For API path |
| `INDEED_CLIENT_ID/SECRET/PUBLISHER_ID` | Indeed API | For API path |
| `GCP_PROJECT_ID`, `GCP_SERVICE_ACCOUNT_KEY`, `GEMINI_API_KEY` | Cloud sync / Gemini | Optional |
| `GOOGLE_CLIENT_ID/SECRET/REFRESH_TOKEN`, `GOOGLE_CALENDAR_ID` | Calendar/Gmail | Optional |
| `TWILIO_ACCOUNT_SID/AUTH_TOKEN/FROM` | SMS notifications | Optional |
| `NGROK_AUTHTOKEN` | Local tunneling only | Optional |
| `WIN_CERT_PATH`, `WIN_CERT_PASSWORD` | Code-signing the .exe | Optional |

## Encrypted fields

- User `email` is encrypted at rest with AES-256-GCM (`security/crypto.py`).
  Key derived from `APP_ENCRYPTION_KEY`. Without a key an ephemeral per-session
  key is used (data won't survive a restart) - always set a real key in `.env`.
- Passwords hashed with PBKDF2-HMAC-SHA256, 600,000 iterations, random salt
  (`security/password.py`).

## Scraping & Terms of Service (IMPORTANT)

- Live scraping of LinkedIn, Indeed, Glassdoor and similar portals may violate
  their **Terms of Service** and can lead to **account suspension or legal
  action**. It is **OFF by default** (`ENABLE_SCRAPING_REAL_SITES=false`).
- The **API-first** paths (LinkedIn Jobs API, Indeed API) are the compliant,
  future-proof routes. Use them whenever credentials are available.
- If you do enable live scraping: keep `automation_speed=human`, use the
  human-like navigation safeguards, respect rate limits/robots.txt, and only
  target sites whose terms permit it. You are solely responsible for compliance.

## Application of least privilege

- The app stores your credentials locally; on submission it uses them transiently.
- No credential is ever sent to a third party except the target job platform.
- Cloud/notification features are opt-in and disabled unless you configure them.

## Build / distribution security

- Unsigned `.exe` may trigger Windows SmartScreen. The GitHub Actions workflow
  runs a Windows Defender scan. For production signing, add your code-signing
  certificate via `WIN_CERT_PATH` and run `build_exe_local.py --sign`
  (signtool). See `docs/REBUILD.md`.
