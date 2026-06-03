# SHARK v18 — Mobile Device Identification System / System Rozpoznawania Urządzeń Mobilnych

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb)](https://www.mongodb.com/)
[![gunicorn](https://img.shields.io/badge/gunicorn-multiworker-499848)](https://gunicorn.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](#)

---

## EN

A browser-fingerprinting API that automatically identifies mobile devices (iOS and Android) and returns warehouse accessory codes (screen protector, case) for the detected model. Designed for production use: modular architecture, MongoDB Atlas, gunicorn multi-worker with atomic writes.

### Detection Pipeline (priority order)

```
1. UA_EXACT       — User-Agent parsed to known model in DB          → 100% confidence
2. UA_CODE        — User-Agent parsed but model not in DB           →  90% confidence
3. AI_FINGERPRINT — Hardware signature matched in learned BRAIN     →  variable
4. HEURISTIC      — Weighted spec scoring; auto-decides if score ≥ 90% and 2nd < 60%
```

### Key Technical Highlights

| Feature | Details |
|---|---|
| **Self-learning AI Brain** | Stores hardware fingerprints (width × height × DPR × GPU × Hz); max 10,000 signatures, LFU eviction |
| **Modular architecture** | Routes · Models · Utils · Config layers; Flask Blueprints |
| **Atomic multi-worker writes** | MongoDB `$set` or `.tmp` + `os.replace` — safe for gunicorn fork model |
| **OS segmentation** | Separate weight sets for iOS vs Android scoring; GPU match 40 pts Android only |
| **Simulation detection** | Flags Intel/Nvidia/Mesa/SwiftShader GPUs as `(symulacja?)` |
| **Rate limiting** | 30 req/min check, 10 req/min learn; Redis-backed for multi-worker |
| **Admin panel** | Brain stats, verified models CRUD, detection logs, MongoDB sync |

### Supported Devices

- **iOS** — iPhone 11 through iPhone 17 Pro Max (27 models)
- **Android** — Samsung Galaxy S/A/Z · Google Pixel · Xiaomi · OnePlus · Huawei (50+ models)

### Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Web Framework | Flask 3.1 + flask-cors |
| Database | MongoDB Atlas (pymongo 4.16) / JSON fallback |
| Production Server | gunicorn 24.1 |
| Rate Limiting | flask-limiter + optional Redis |
| Testing | pytest + pytest-mock |

### API

```
POST /api/check_brain   — identify device from fingerprint
POST /api/learn         — teach a new fingerprint → model mapping
GET  /admin             — admin panel (MongoDB required)
```

Request:
```json
{
  "w": 390, "h": 844, "hz": 60, "dpr": 3.0,
  "gpu": "Apple GPU", "canvasHash": "abc123",
  "ram": -1, "cores": 6,
  "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 ...)",
  "dprVerified": true, "isZoomed": false
}
```

Response:
```json
{
  "found": true,
  "model": "iPhone 15",
  "confidence": 100,
  "source": "UA_EXACT",
  "codes": { "screen": "AP1234", "case": "AP5678" },
  "detection_log": {}
}
```

### Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env   # set MONGODB_URI or leave blank for JSON fallback
python shark_v18_cloud.py
# Production: gunicorn shark_v18_cloud:app
```

### Repository Structure

```
app/
├── config.py          # Central config, logging
├── database.py        # MongoDB / JSON init, atomic save
├── models/            # Static identifiers, heuristic DB, accessory codes
├── routes/            # Flask blueprints (API + admin)
└── utils/             # Core algorithms, validators
```

---

## PL

API do automatycznego rozpoznawania urządzeń mobilnych (iOS i Android) z wykorzystaniem fingerprintingu przeglądarki. Zwraca kody magazynowe akcesoriów (szkło ochronne, etui) dla wykrytego modelu. Produkcyjna architektura: moduły Flask, MongoDB Atlas, gunicorn multi-worker z atomicznymi zapisami.

### Potok detekcji

```
1. UA_EXACT       — UA dopasowany do modelu w DB              → pewność 100%
2. UA_CODE        — UA dopasowany, model poza DB              → pewność 90%
3. AI_FINGERPRINT — sygnatura sprzętowa w słowniku BRAIN      → zmienna
4. HEURISTIC      — scoring ważony; auto-decyzja przy ≥ 90% i 2. < 60%
```

### Szybki start

```bash
pip install -r requirements.txt
cp .env.example .env   # ustaw MONGODB_URI lub zostaw puste (tryb JSON)
python shark_v18_cloud.py
```

---

## License / Licencja

Proprietary — all rights reserved.
