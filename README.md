# AI Job Hunter

Personal AI job-discovery and application assistant. All six phases are implemented.

## Quick start (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

Opens http://localhost:3000. Password = `DASHBOARD_PASSWORD` in `.env`.

## Daily workflow

One-time setup in **Settings → Sources & email**: add Google Alerts RSS feeds, Telegram channels and/or company boards (Lever, Greenhouse), and your mailbox (Gmail App Password) for email applications. Then **Agent Control → Start agent**.

After that the agent works on its own:

1. **Discovery**: every few hours (default 6) and at the daily 08:00 (Asia/Jakarta) run, new listings are fetched from the enabled sources and de-duplicated.
2. **Analysis**: score, hard filters and recommendation (auto-apply eligible / review / skip / reject).
3. **Documents**: a tailored CV + cover letter (PDF & DOCX), application email and form answers for each eligible job.
4. **Apply**, within the daily limit, eligible jobs only:
   - listing asks for an email application → sent from your mailbox with the documents attached;
   - employer application form (e.g. Lever / Greenhouse hosted page) → filled and submitted by the browser, stopping on anything unverified;
   - everything else waits for you (review queue / assisted apply).
5. **Notification** with the run summary (bell icon, optional webhook).

You check **Applications** (table/Kanban) and update statuses (interview, assessment, rejected, accepted).

## Status

| Phase | Scope | Status |
|---|---|---|
| 1 | Backend, DB + migrations, auth, dashboard, CV import & profile editor | ✅ |
| 2 | Discovery: Google Alerts RSS, Telegram channels, Lever & Greenhouse public APIs; URL normalization, dedup | ✅ |
| 3 | Matching engine, hard filters, explanations | ✅ |
| 4 | Tailored CV / cover letter (PDF+DOCX), email, form answers, versioning | ✅ |
| 5 | Apply by email (SMTP) and by browser (auto / assisted), safety stops, confirmation tracking | ✅ |
| 6 | APScheduler daily runs, retries, crash recovery, notifications, Docker | ✅ |

No integration is simulated; statistics come only from real DB rows.

## Layout

```
backend/            FastAPI app (Python)
  app/api/          HTTP routes (auth, candidate, jobs, documents, apply, agent, settings, dashboard)
  app/core/         settings, auth/session, encryption, PII-redacting logging
  app/models/       SQLAlchemy models
  app/schemas/      Pydantic schemas
  app/services/     cv_* (import), matching/ (Phase 3), documents/ (4), apply/ (5), agent/ (6), notifications
  app/sources/      JobSourceAdapter interface + registry (portal adapters plug in here)
  migrations/       Alembic migrations
  scripts/          import_cv.py, smoke_test.py + smoke_phases.py (live end-to-end checks, self-cleaning)
  tests/            pytest suite (synthetic fictional CVs only)
frontend/           Next.js 16 + TypeScript + Tailwind v4, shadcn-style components
config/             preferences.json, sources.json, scheduler.json (mirrors of DB settings)
                    candidate.json is generated from your CV and git-ignored
data/               SQLite DB (local dev), original CVs — git-ignored, contains personal data
```

## Local development (Windows)

Prerequisites: Python 3.12+, Node 20+. PostgreSQL optional for local dev (SQLite fallback).

```powershell
# 1. Configure secrets (once)
Copy-Item .env.example .env   # then set APP_SECRET_KEY (>=32 chars) and DASHBOARD_PASSWORD (>=8)

# 2. Backend
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m uvicorn app.main:app --port 8000 --reload

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev        # http://localhost:3000
```

The browser only talks to Next.js; `/api/*` is rewritten to the backend (`BACKEND_URL`, default `http://127.0.0.1:8000`) so the session cookie stays first-party.

### Importing a CV

Dashboard: **Settings → Candidate profile → Upload CV**, or CLI:

```powershell
cd backend
.venv\Scripts\python -m scripts.import_cv "C:\path\to\cv.pdf"
```

The original file is stored once under `data/cv/originals/<sha256>.pdf` and never overwritten. Each import creates a new **unconfirmed** profile version; earlier versions stay in `candidate_profile_versions`. The profile can only be confirmed when no critical question is open.

### Tests

```powershell
cd backend
.venv\Scripts\python -m pytest            # unit + API tests
.venv\Scripts\python -m scripts.smoke_test    # requires both servers running
.venv\Scripts\python -m scripts.smoke_phases  # phases 3-6 end to end; removes its test data afterwards

cd frontend
npx next typegen; npx tsc --noEmit; npx eslint .; npm run build
```

## Docker

```powershell
# .env must also contain POSTGRES_PASSWORD
docker compose up --build    # dashboard on http://localhost:3000 (bound to 127.0.0.1)
```

The backend runs `alembic upgrade head` on start and uses PostgreSQL. `./data` and `./config` are mounted volumes.

## Security notes

- Single-owner dashboard: password login → HMAC-signed, httpOnly, SameSite=strict session cookie (12 h default). Five failed logins lock a client for 5 minutes.
- All API routes except `/api/health` and `/api/auth/login` require auth; the Next.js proxy only handles redirects.
- AI API keys entered in the dashboard are Fernet-encrypted (key derived from `APP_SECRET_KEY`) and only shown masked. Environment keys are never written to the DB.
- Logs pass through a redaction filter (emails, phone numbers, tokens, keys).
- `.env`, `data/`, `config/candidate.json` are git-ignored. Changing `APP_SECRET_KEY` invalidates sessions and stored encrypted keys.

## Ingestion rules (all sources)

`backend/app/services/job_ingestion.py`, `job_normalize.py`:

- URLs are normalised (https, lowercase host, no trailing slash, tracking params such as `utm_*`, `ref`, `gh_src` removed). `jobstreet.com` URLs are rejected: JobStreet was removed as a source because its robots.txt and Cloudflare block automated access (checked 2026-11-11) and SEEK's API is for employers only.
- A listing is a duplicate when the canonical URL **or** `(source, external_id)` matches (e.g. `telegram:<channel>/<post>`, `lever:<company>:<id>`); the existing row is updated instead of adding one. Refreshes never replace a longer description or a disclosed salary with poorer data; manual edits always overwrite.
- Salary: structured API values are used as-is; text labels are parsed only when clearly IDR (`Rp`, `IDR`, or `jt/juta`) with a period, or a `jt` amount (read as monthly). Annual/weekly/daily are converted to monthly. Anything else stays **undisclosed**.
- Each new listing gets a tracking record with status `discovered`.

## Matching engine (Phase 3)

Code: `backend/app/services/matching/`. Everything that decides is deterministic Python; an LLM is used only to write optional prose.

| Component | Weight | How it is scored |
|---|---|---|
| Technical skills | 35% | Skills detected in the listing (EN + ID vocabulary) vs. profile skills. Mandatory skills count 2×, "nice to have" 0.5×. |
| Work experience | 25% | Half: years in profile vs. stated minimum (fresh-graduate listings = full marks). Half: share of past roles that mention the listing's skills. |
| Job title | 15% | Title category vs. your selected target categories (100) / categories supported by your CV (85) / unsupported (10). |
| Education | 10% | Lowest level mentioned (e.g. "D3/S1" → D3) vs. your highest degree; not-yet-completed degree = 75. |
| Location & arrangement | 10% | Greater-Jakarta aliases (Jaksel, South Jakarta, BSD, Cikarang, SCBD…). Unknown = 60. |
| Salary | 5% | Range ≥ minimum = 100; straddles minimum = 70; undisclosed = 0. |

**Hard filters (reject regardless of score):** disclosed salary whose maximum is below the minimum; location outside the list; fully remote (also detected from the description) while remote is disabled; work arrangement or employment type not in preferences; mandatory skills missing from the profile; mandatory education not met; experience below half the stated years; job title in a category the CV does not support; already applied.

**Recommendation:** any hard-filter failure → `reject`. Score ≥ auto-apply threshold (85) **and** salary, location and arrangement all verified → `auto_apply_eligible`. Score ≥ review threshold (70), or ≥ 85 but with something unverified → `review` (undisclosed-salary jobs go to `skip` if that review queue is disabled). Otherwise → `skip`.

The engine sets application status only while it is `discovered/analyzed/qualified/rejected`; it never overrides a status you set. Re-importing a listing clears its old analysis. Analysis requires a **confirmed** profile.

**AI explanation (optional):** `POST /api/jobs/{id}/analyze {"with_ai": true}` calls `{AI_BASE_URL}/chat/completions` (OpenAI-compatible) with the engine result, the job text, and an anonymised profile (no name, email, phone, website or domicile). The reply is stored as text only and never parsed back into the decision.

**Manual status updates:** marking a job `applied` requires your own confirmation text (e.g. the confirmation email date); interview/assessment/accepted require `applied` first.

## Sources and automatic discovery

JobStreet and its capture/browser scraper have been removed. The app never scrapes a portal that blocks automation.

**Google Alerts RSS:** go to `google.com/alerts`, create alerts such as `"lowongan admin marketplace" jakarta`, Show options → **Deliver to: RSS feed**, then add each feed URL in Settings → Sources & email. The app reads the feed and keeps the linked page as a summary-only listing; it does not scrape the linked site.

**Telegram:** add public `@channel` usernames in Settings. Public preview mode uses `https://t.me/s/<channel>` (read-only). Recommended API mode: create an app at `my.telegram.org` → API development tools, connect your own Telegram account in Settings with the code Telegram sends. The API session is encrypted. The app only reads chosen channels; it never joins, posts, messages or broadcasts. Telegram's official FAQ says bots receive channel messages only where they are members; using your own account is required for arbitrary public channels. Scam markers (fees, deposits, "no interview") are flagged.

**Company APIs:** add company board tokens in Settings → Sources & email. Lever public endpoint: `https://api.lever.co/v0/postings/<company>?mode=json`. Greenhouse public endpoint: `https://boards-api.greenhouse.io/v1/boards/<company>/jobs?content=true`. These APIs are designed to publish jobs; the public GET endpoints need no key. Applications can only be submitted where the employer's application policy permits it. Lever's POST application endpoint needs an API key generated by that employer's Super Admin, so this personal app does not pretend it can submit to arbitrary Lever boards.

The agent fetches enabled sources every configured interval (default 6 hours) and at the daily run. It respects robots.txt, identifies itself, rate-limits requests, stops on 403/429, and never rotates IPs or bypasses protections. New rows show source, source notes and apply method.

## Documents (Phase 4)

`backend/app/services/documents/`. Content comes only from the confirmed profile: job keywords reorder skills, skill groups and bullets and fill the "Relevant skills" line with skills **you already have**; nothing is added or rephrased. Profile sentences are quoted verbatim, so documents default to the profile's language (choose EN/ID per generation; the letter frame is translated, your bullets are not). Two single-column ATS templates (`classic`, `modern`), real selectable text, no tables/images in DOCX. Each generation is a new version in `data/documents/app_<id>/v<n>/` (CV PDF/DOCX, cover letter PDF/DOCX, `application_email.txt`, `form_answers.json`); answers without a verified fact are marked `REQUIRES YOUR INPUT`.

## Application engine (Phase 5)

`backend/app/services/apply/`. Flow: open page → closed/already-applied check → CAPTCHA / login / OTP detection → open the form (one clear "Apply" button) → detect fields → map to verified facts → fill/upload → (auto mode only) validate → submit → require on-page confirmation text.

Always enforced:

- CAPTCHA, anti-bot walls, login and OTP are **detected and stop the run**; they are never bypassed. The persistent browser profile (`data/browser_profile/`) lets *you* log in once yourself; the app never sees your password.
- Sensitive fields (NIK/KTP, NPWP, bank, religion, date of birth, gender, photo, passwords…), legal declarations/consent checkboxes, salary history and unknown free-text questions are never filled; if required, the run stops (auto) or lists them for you (assisted).
- Yes/No answers are only chosen when exactly one option matches your recorded fact.
- `applied` is set only with confirmation evidence (page text in auto mode, your own confirmation text otherwise). No confirmation → `pending_action`, never "success".
- Failures save a viewport-only screenshot (`data/screenshots/`); stored attempt logs contain field *labels* only, never values.
- One browser automation at a time; duplicates and already-applied jobs are refused.

**Apply methods** (`policy.py`), tried in this order by the agent for `auto_apply_eligible` jobs when `auto_apply` is on, within `daily_application_limit`:

- **email** – the listing names an address ("kirim CV ke hrd@…", typical on Telegram). Sent from your own mailbox via SMTP with the latest CV and cover letter PDFs. Recorded as applied only after the mail server accepts the message; a job is never emailed twice.
- **auto** – unattended browser submission on the employer's own form. Not offered for hosts that block automation (JobStreet, LinkedIn, Indeed, Glints).
- **assisted** – browser pre-fills verified fields, you review and submit. Always available as a fallback for any form.

Telegram posts and Google redirect links are not forms; such jobs can only be applied to by email (if an address is given) or by you.

## Scheduler & notifications (Phase 6)

`backend/app/services/agent/`. APScheduler runs inside the backend (`ENABLE_SCHEDULER=true`) with a cron trigger at the configured time in Asia/Jakarta. Guarantees: one run at a time (APScheduler `max_instances=1` plus a DB check covering manual runs and multiple processes); per-day idempotency keys; runs left `running` by a crash are marked failed on startup (heartbeat timeout 30 min); failed scheduled runs retry with exponential backoff (60 s, 120 s, 240 s… up to `max_retries`); pause/resume/start from Agent Control. Discovery steps that have no permitted adapter are reported as skipped, not faked.

Notifications are always stored for the dashboard (bell icon). Set `NOTIFY_WEBHOOK_URL` to also POST `{"title","body","level","content"}` to a webhook (Discord-compatible `content` field).

## Limitations

- Google Alerts gives a title/snippet/link, not a guaranteed full job description. Open the linked page yourself if you need more context; the app does not scrape it automatically.
- Telegram posts are unstructured. Unknown salary, company, location or questions stay empty; scam indicators are warnings, not proof.
- Lever and Greenhouse APIs publish jobs, but arbitrary candidate submission is not available: Lever requires the employer's API key; Greenhouse requires the employer's Job Board API key for POST. The app uses public GET discovery and auto-applies only on employer forms where the site permits it.
- Source feeds/APIs may return old, closed or duplicate listings; lookback and stable IDs reduce this, but status must be checked before applying.
- Email applications use the generated email text; listings that ask for a specific subject line or extra documents (KTP, ijazah…) need your attention. Check the source note before enabling auto-apply for a channel.
- Form detection is heuristic. Unusual multi-step forms or custom widgets may stop with "no form detected" / "unresolved fields"; that is the safe failure mode.
- CV parsing has no OCR; certifications/projects are entered manually. Skill vocabulary is ~60 skills (profile skills always count).
- AI explanations were tested against a mocked provider only; configure `AI_*` to use a real one.
- Assisted apply needs a desktop session (visible browser). In Docker the browser is headless, so use assisted apply from the local Windows install.
- Login throttling is in-memory. Docker files were written but not executed here (Docker not installed).
