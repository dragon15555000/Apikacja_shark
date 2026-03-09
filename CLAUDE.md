# CLAUDE.md — SHARK v18 Codebase Guide

## Project Overview

**SHARK v18** is a mobile device identification system using browser fingerprinting and AI. It identifies iOS and Android phones/tablets and returns accessory codes (screen protector, case codes) for the identified device.

Current version: **18.33** ("Modular Architecture Refactor")

### Detection Pipeline (priority order)

1. **UA_EXACT** (100% confidence) — User-Agent parsed to a known identifier, found in device DB
2. **UA_CODE** (90% confidence) — User-Agent parsed to an identifier, not in DB but returned as-is
3. **AI_FINGERPRINT** (variable) — Hardware signature matched in the learned `BRAIN` dictionary
4. **HEURISTIC_AUTO** / **HEURISTIC_TOP3** — Weighted scoring against `HEURISTIC_DB`; auto-decides if top ≥ 90% and second < 60%

---

## Repository Structure

```
/
├── shark_v18_cloud.py          # PRODUCTION entry point (used by Procfile/gunicorn)
├── shark_v18.py                # Standalone legacy entry point (local dev)
├── main.py                     # Empty placeholder
├── Procfile                    # Heroku/Render: gunicorn shark_v18_cloud:app
├── runtime.txt                 # Python 3.13.4
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
│
├── app/                        # Main application package
│   ├── __init__.py             # Package init (version: 18.23)
│   ├── config.py               # Central config (VERSION, DB settings, logging)
│   ├── database.py             # DB init, BRAIN/EXTERNAL_DB loading, atomic save
│   ├── logic.py                # Re-export shim (imports from utils/logic.py)
│   │
│   ├── models/                 # Static data / identifier databases
│   │   ├── identifiers.py      # STATIC_IDENTIFIERS (iOS UA codes → model names)
│   │   ├── android_identifiers.py  # ANDROID_IDENTIFIERS (SM-XXXX, etc.)
│   │   ├── static_identifiers.py   # Additional static mappings
│   │   ├── heuristic_db.py     # HEURISTIC_DB (specs for weighted scoring)
│   │   ├── iphone_specs.py     # iPhone hardware specs
│   │   └── accessory_codes.py  # ACCESSORY_CODES (model → {screen, case})
│   │       (also: __init__.py imports ACCESSORY_CODES from here)
│   │
│   ├── routes/                 # Flask route registration
│   │   ├── api_routes.py       # /api/check_brain, /api/learn
│   │   └── admin_routes.py     # /admin, /admin/api/*
│   │
│   └── utils/
│       ├── logic.py            # Core algorithms: build_signature, normalize_viewport,
│       │                       #   parse_device_from_ua, find_top_3_matches
│       └── validators.py       # @validate_json decorator
│
├── templates/
│   ├── index.html              # Main client UI (sends fingerprint to /api/check_brain)
│   └── admin.html              # Admin panel (requires MongoDB)
│
├── tests/
│   ├── __init__.py
│   ├── test_logic.py           # Unit tests for parse_device_from_ua, find_top_3_matches
│   ├── test_logic_advanced.py  # Advanced unit tests
│   └── test_logic_simple.py    # Simple unit tests
│
├── shark_external_db.json      # Large external device identifier DB (Matomo-sourced)
├── custom_models.json          # Custom model additions
├── setup_database.py           # CLI: imports Matomo device DB into MongoDB
├── add_missing_models.py       # CLI: adds missing model entries
├── import_verified_models.py   # CLI: imports verified models
├── migrate_to_mongodb.py       # CLI: migrates JSON brain to MongoDB
└── run_matcher.py              # CLI: test matching logic
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13.4 |
| Web framework | Flask 3.1.2 |
| CORS | flask-cors 6.0.2 |
| Rate limiting | flask-limiter 4.1.1 |
| Database | MongoDB (pymongo 4.16.0) or JSON file fallback |
| Production server | gunicorn 24.1.1 |
| Testing | pytest 8.3.2 + pytest-mock 3.14.0 |

---

## Environment Variables

Copy `.env.example` to `.env` for local development:

```bash
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=shark_db
PORT=5000

# Optional
REDIS_URI=redis://...    # For multi-worker rate limiter; falls back to in-memory
HOST=0.0.0.0
DEBUG=False
```

If `MONGODB_URI` is not set, the app falls back to JSON file storage (`shark_brain_v18.json`).

---

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Local development (JSON file storage)
python shark_v18_cloud.py

# Production (gunicorn, as per Procfile)
gunicorn shark_v18_cloud:app

# Legacy single-file runner
python shark_v18.py
```

App runs on `http://0.0.0.0:5000` by default.

---

## Running Tests

```bash
# Run all tests
pytest tests/

# Run a specific test file
pytest tests/test_logic.py -v

# Run with output
pytest tests/ -s
```

Tests use `pytest-mock` to patch `app.logic.db = None` so the scoring algorithms use only `HEURISTIC_DB` without a live MongoDB connection.

**Important:** `tests/test_logic.py` imports from `app.logic` (the re-export shim), not directly from `app.utils.logic`. Keep that shim intact.

---

## API Endpoints

### `POST /api/check_brain`
Rate limit: 30/minute

Request body (all required):
```json
{
  "w": 390, "h": 844, "hz": 60, "gpu": "Apple GPU",
  "canvasHash": "abc123", "dpr": 3.0, "ram": -1, "cores": 6,
  "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)...",
  "dprVerified": true, "isZoomed": false
}
```

Response (found):
```json
{
  "found": true, "model": "iPhone 15",
  "confidence": 100, "source": "UA_EXACT",
  "codes": {"screen": "AP1234", "case": "AP5678"},
  "detection_log": { ... }
}
```

Response (not found):
```json
{
  "found": false, "suggestions": [...],
  "codes": {"screen": "N/A", "case": "N/A"},
  "detection_log": { ... }
}
```

### `POST /api/learn`
Rate limit: 10/minute. Teaches the AI brain a fingerprint → model mapping.

Required: same as `check_brain` plus `"model": "iPhone 15"`.

### `GET /admin` (requires MongoDB)
Admin panel HTML. Provides brain stats, verified models CRUD, detection logs.

### `GET/POST /admin/api/*`
Admin REST API — brain stats, clear, verified-models CRUD, detection logs, export, MongoDB sync.

---

## Key Algorithms

### `build_signature(width, height, dpr, ram, refresh_rate, gpu, canvas_hash)`
Returns a canonical string key: `"{w}_{h}_{dpr}_{ram}_{hz}_{gpu}"`.
`canvas_hash` is intentionally **not included** so the same phone gets the same signature across Chrome/Safari/Firefox.

### `normalize_viewport(width, height)`
Rounds dimensions if within 0.02 of an integer (eliminates floating-point noise).

### `parse_device_from_ua(ua)`
Regex-based extraction supporting: iPhone/iPad, Samsung (SM-XXXX), Google Pixel, Xiaomi, OnePlus (CPH/LE/IN/NE), Huawei/Honor, Motorola (XT-codes, moto names).

### `find_top_3_matches(...)`
Weighted scoring with OS segmentation (iOS vs Android). Key weights:
- GPU match: 40 pts (Android only)
- Width exact: 50 pts (iOS) / 20 pts (Android)
- Height exact: 30 pts (iOS) / 10 pts (Android)
- DPR exact: 20 pts (iOS) / 25 pts (Android)
- Hz match: +15/+5 pts; Hz mismatch: -20/-10 pts penalty
- RAM: +5 pts (Android only)

Simulation detection: if GPU contains "intel", "nvidia", "amd", "angle", "swiftshader", or "mesa", the result is flagged as `(symulacja?)`.

---

## Data Storage

### BRAIN (AI fingerprint memory)
- **MongoDB**: collection `brain`, single document `{_id: 'brain_v18', data: {...}}`
- **Fallback**: `shark_brain_v18.json` (written atomically via `.tmp` + `os.replace`)
- Limits: max 10,000 signatures, max 5 models per signature (LFU eviction)
- **Atomic save**: `save_brain_signature(sig, model_data)` uses MongoDB `$set` or atomic file write — safe for gunicorn multi-worker

### EXTERNAL_DB (device identifiers)
Merged at startup: `STATIC_IDENTIFIERS` + `ANDROID_IDENTIFIERS` + `shark_external_db.json` (or MongoDB `external_db` collection).

### Detection Logs
MongoDB only — collection `detection_logs`. Not persisted in JSON mode.

---

## Adding a New Device

### 1. Add UA identifier mapping
Edit `app/models/android_identifiers.py` (Android) or `app/models/identifiers.py` (iOS):
```python
ANDROID_IDENTIFIERS = {
    "SM-X123": "Samsung Galaxy NEW MODEL",
}
```

### 2. Add accessory codes
Edit `app/models/accessory_codes.py` (or the `__init__.py` that exposes `ACCESSORY_CODES`):
```python
ACCESSORY_CODES = {
    "Samsung Galaxy NEW MODEL": {"screen": "SA_SCREEN_CODE", "case": "SA_CASE_CODE"},
}
```

### 3. Add heuristic specs (for fingerprint fallback)
Edit `app/models/heuristic_db.py`:
```python
HEURISTIC_DB = {
    "Samsung Galaxy NEW MODEL": {"w": 412, "h": 915, "dpr": 3.0, "ram": 8, "hz": 120, "gpu": "adreno 740"},
}
```

---

## Code Conventions

- **Language**: All code comments and docstrings may be in Polish (`pl`) or English — both exist in the codebase.
- **Logging**: Use the module-level `logger = logging.getLogger('shark_app')` from `app/config.py`. Emoji prefixes are used in log messages (e.g., `✅`, `❌`, `📍`, `🧠`).
- **Error handling**: All route handlers use `try/except Exception` with `logger.error(..., exc_info=True)` and return `500`.
- **Validation**: Use the `@validate_json(*fields)` decorator from `app/utils/validators.py` for required field checks. Add manual type/range validation inside the handler.
- **Route registration**: Routes are registered via `register_api_routes(app, limiter)` and `register_admin_routes(app)` functions — do not use `@app.route` directly in new files.
- **Config import**: Always import settings from `app.config`, never hardcode env var names or defaults elsewhere.
- **DB imports**: Use `from app.database import ...` for collections and helper functions. Never import `pymongo` directly in route/logic files.
- **Atomic writes**: Always use `save_brain_signature()` (not `save_brain()`) when updating a single signature to remain multi-worker safe.

---

## Deployment

Production is deployed via `Procfile`:
```
web: gunicorn shark_v18_cloud:app
```

Supported platforms: Heroku, Render. See `DEPLOY_CLOUD.md`, `QUICK_DEPLOY.md` for step-by-step guides.

**Required env vars for production**: `MONGODB_URI`, `MONGODB_DB`.
**Recommended**: `REDIS_URI` for rate limiter state sharing across workers.

---

## File Notes

- `shark_v18_cloud_BACKUP.py` — backup of the pre-refactor monolithic file; do not edit
- `shark_external_db.json` — ~530KB external device DB; do not commit changes to this file manually, use `setup_database.py`
- `shark_brain_v18.json` — gitignored; runtime-generated AI brain file
- `main.py` — empty; exists as a placeholder
