# ScamShield

A working academic prototype based on the supplied AI Scam Message Detector specification. The package includes a Flutter mobile client, FastAPI API, PostgreSQL configuration, a browser client, synthetic ML baseline, automated backend tests, and requirements mapping.

## What you can use

- **Hosted browser demo:** local message checking, screenshot OCR, optional history, illustrative feed, local posts/comments/receipts. It does not connect to a live community, run the trained Python model, or issue trusted verification.
- **Full project running locally:** the browser client automatically connects to FastAPI on the same origin. This enables the trained baseline, accounts, shared database-backed reports/comments/receipts, and authorised reviewer decisions.
- **Flutter source:** mobile flows use the same backend and on-device ML Kit OCR. Android/iOS wrappers are generated with the setup script. No compiled APK/IPA is included. Flutter and native builds were not available in the authoring environment and must be validated on your machine.

## Quick start — browser and backend without Docker

Install Python 3.12 or newer, then open a terminal in this extracted folder:

```sh
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```sh
source .venv/bin/activate
```

Then:

```sh
python -m pip install -r backend/requirements.txt
cd backend
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000 --no-access-log
```

Open **http://127.0.0.1:8000**. The top-right badge should say **Backend connected**. API documentation is at **http://127.0.0.1:8000/docs**. The simple path uses SQLite, creating `backend/scamshield.db`. It has the same API and SQLAlchemy models as the PostgreSQL configuration below.

## PostgreSQL version with Docker

From the project root, copy `.env.example` to `.env` and replace the sample password with a random alphanumeric password. Docker Desktop must be installed and running.

```sh
docker compose up --build
```

Open **http://127.0.0.1:8000**. PostgreSQL keeps its records in a Docker volume. The database port is not exposed. The web port is bound to loopback. This is a local development setup; use TLS and appropriate proxy limits before remote deployment.

## Try the full flow

1. Open the app and choose the Banking sample. Analyse it and inspect four separate evidence panels.
2. Save an analysis, open History, reopen it, then delete it.
3. Click the account control and create a username/password. Passwords require 10 characters. No email or password-reset flow is included.
4. Publish a report after redacting names, contact details, addresses and codes. The server also removes email addresses and long numbers.
5. Open that report, comment, and mark it received. Receipts are unique per authenticated account and report. The creator's receipt is already counted.
6. Request review. The report enters the reviewer queue.
7. Create a separate reviewer account through the same registration flow, then provision it using the operator command below. Registration can never self-assign a reviewer role.
8. Sign in again with the reviewer account, open Trusted review, and record a decision with a rationale. The server writes the decision and audit record in one transaction.

For local Python setup, in `backend/`:

```sh
python manage.py promote-reviewer your_reviewer_username
```

For Docker, from the root:

```sh
docker compose exec api python manage.py promote-reviewer your_reviewer_username
```

Use `revoke-reviewer` instead of `promote-reviewer` to remove the role. Do not expose this operator command through a public HTTP endpoint.

## Flutter mobile client

Install Flutter stable, an Android SDK/emulator, and (for iOS) macOS with Xcode and CocoaPods. From the project root:

```sh
python scripts/setup_mobile.py
cd mobile
flutter analyze
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api
```

`10.0.2.2` connects an Android emulator to the host machine's localhost. Android debug builds allow HTTP for this local development path; release builds do not. The supplied script sets Android minSdk 23, iOS minimum 15.5, internet access, and the photo-library purpose string. Resolve any newer Flutter/plugin platform constraints reported by your installed SDK before building.

For an iPhone/iOS simulator or physical Android device, provide an **HTTPS** backend URL reachable by that device:

```sh
flutter run --dart-define=API_BASE_URL=https://your-backend.example/api
```

The example host is a placeholder, not a deployed service. Do not enter it unchanged. The local Docker API is deliberately not reachable from other devices without a separate secure deployment. Native OCR is Android/iOS only, not Flutter Web. The independent `web/` client uses browser OCR.

### Architecture

- `mobile/lib/repositories.dart`: interfaces for OCR, classifier, intelligence and history; HTTP, ML Kit, local history and secure session implementations.
- `mobile/lib/view_model.dart`: `AnalyzeMessageUseCase` and `SubmitMessageViewModel`; views do not invoke OCR/model logic directly.
- `mobile/lib/main.dart`: check/result, community, history, account, report detail and trusted review views.
- `backend/intelligence.py`: separate indicator extraction, redaction, synthetic-trained classifier and historical matching.
- `backend/app.py`: persistence, authentication, validation, community endpoints and role-enforced verification with audit records.
- `web/`: responsive browser client; automatically detects a backend when served by FastAPI.

The prototype combines verification orchestration into backend service functions; it does not yet implement every named class from the conceptual UML as a separate class. Matching uses exact URLs and token overlap; it is not a live blacklist or embedding search. Report listing and matching are capped at 200 recent records and need pagination/indexing for larger datasets.

## Tests and evaluation

From `backend/`:

```sh
python -m pytest -q
python evaluate.py
```

The backend suite passed **16 tests** in this environment. Tests cover input validation, classification response, indicators, missing matches, redaction, authenticated reporting, role injection, unique receipts, comments, reviewer controls/audit, evidence precedence, no analysis retention, service failures and logout. Tested with SQLite; PostgreSQL integration and native device tests are pending.

`docs/evaluation.json` records a tiny synthetic holdout evaluation and local classification latency. These scores are only a smoke test. Do not report them as evidence of real-world accuracy. The <=5-second network target, OCR correctness on devices and usability targets have not been measured. See `docs/REQUIREMENTS.md` for the full acceptance status.

## Privacy and limitations

Screenshots are never accepted by the backend; clients extract text on-device. The selected image remains in your photo library, while the Flutter picker cache copy is removed after extraction. Browser OCR downloads Tesseract software/language assets from a CDN and may fail when offline or blocked. Extracted text remains editable until you explicitly analyse it.

The analysis endpoint does not persist submitted text. History is opt-in and device-local, not cloud-synced or encrypted by the app; use only redacted content on shared devices. Public reports/comments are intentionally persistent and redacted; review personal details manually because pattern-based redaction cannot find everything. Raw image evidence is not published: report evidence consists of redacted text and detected indicators.

The backend model is trained on 32 synthetic messages at startup. It is a replaceable baseline, not a production detector. It uses TF-IDF/logistic regression plus heuristic cues. Its risk index is not a calibrated probability. Rule cues explain the heuristic component, not individual learned model coefficients. High community counts never change verification. A verified similar report does not verify a newly submitted message.

Passwords are salted with PBKDF2-SHA256 (600,000 iterations). Tokens are random, stored hashed server-side, expire after 24 hours, and are revocable by logout. Flutter stores tokens in secure storage; the browser keeps tokens in memory. Account creation/login has a per-process limiter. Add distributed limits, migration management, abuse moderation, account recovery, monitoring, backups and independent security testing before wider use. Multiple fake accounts remain a risk; unique-per-account does not mean unique-per-person.

## Primary implementation references

- Flutter: https://docs.flutter.dev/
- ML Kit Flutter plugin: https://pub.dev/packages/google_mlkit_text_recognition
- Image picker: https://pub.dev/packages/image_picker
- FastAPI authentication: https://fastapi.tiangolo.com/reference/security/
- FastAPI tests: https://fastapi.tiangolo.com/tutorial/testing/
