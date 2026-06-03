# SHARK v18 — Mobile Device Identification System / System Rozpoznawania Urządzeń Mobilnych

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](#)

---

## EN

Browser-fingerprinting system for automatic mobile device identification (iOS and Android). Identifies the device model and returns accessory codes (screen protectors, cases) via a REST API.

### Detection Pipeline

| Priority | Method | Confidence |
|---|---|---|
| 1 | User-Agent exact match | 100% |
| 2 | User-Agent code (not in DB) | 90% |
| 3 | AI Brain — learned hardware signatures | variable |
| 4 | Heuristic scoring (weighted specs) | 60–85% |

### Key Features

- **Multi-layer detection** — UA parsing → AI Brain → weighted heuristics
- **AI Brain** — self-learning fingerprint dictionary; stores up to 10,000 signatures, 5 models per signature
- **Supported devices** — 27 iPhone models (11–17 series), 50+ Android models (Samsung, Google Pixel, Xiaomi, OnePlus, Huawei)
- **Accessory codes** — automatic lookup of screen protector and case stock codes per model
- **MongoDB + JSON fallback** — production uses Atlas; local dev uses a JSON file
- **Rate limiting** — 30 req/min on check, 10 req/min on learn
- **Atomic writes** — safe for gunicorn multi-worker deployment

### Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Web Framework | Flask 3.1 |
| Database | MongoDB (pymongo) / JSON fallback |
| Production Server | gunicorn |
| Rate Limiting | flask-limiter |

### API

```
POST /api/check_brain   — identify device
POST /api/learn         — teach a new fingerprint
GET  /admin             — admin panel (MongoDB required)
```

Example request:
```json
{
  "w": 390, "h": 844, "hz": 60, "dpr": 3.0,
  "gpu": "Apple GPU", "canvasHash": "abc123",
  "ram": -1, "cores": 6,
  "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 ...)"
}
```

Example response:
```json
{
  "found": true,
  "model": "iPhone 15",
  "confidence": 100,
  "source": "UA_EXACT",
  "codes": { "screen": "AP1234", "case": "AP5678" }
}
```

### Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env   # set MONGODB_URI or leave blank for JSON mode
python shark_v18_cloud.py
```

---

## PL

System do automatycznego rozpoznawania urządzeń mobilnych (iOS i Android) z wykorzystaniem fingerprintingu przeglądarki. Identyfikuje model urządzenia i zwraca kody akcesoriów (szkła ochronne, etui) przez REST API.

### Potok detekcji

| Priorytet | Metoda | Pewność |
|---|---|---|
| 1 | Dokładne dopasowanie User-Agent | 100% |
| 2 | Kod z User-Agent (brak w DB) | 90% |
| 3 | AI Brain — nauczone sygnatury sprzętowe | zmienna |
| 4 | Scoring heurystyczny (ważone specyfikacje) | 60–85% |

### Główne funkcje

- **Detekcja wielowarstwowa** — parsowanie UA → AI Brain → heurystyki
- **AI Brain** — słownik fingerprintów; maks. 10 000 sygnatur, 5 modeli na sygnaturę
- **Obsługiwane urządzenia** — 27 modeli iPhone (serie 11–17), 50+ Android (Samsung, Google Pixel, Xiaomi, OnePlus, Huawei)
- **Kody akcesoriów** — automatyczne wyszukiwanie kodów szkła i etui dla każdego modelu
- **MongoDB + fallback JSON** — produkcja na Atlas; dev lokalny używa pliku JSON
- **Rate limiting** — 30 req/min na sprawdzanie, 10 req/min na uczenie
- **Atomic writes** — bezpieczne dla wieloprocesowego gunicorn

### Szybki start

```bash
pip install -r requirements.txt
cp .env.example .env   # ustaw MONGODB_URI lub zostaw puste (tryb JSON)
python shark_v18_cloud.py
```

---

## License / Licencja

Proprietary — all rights reserved.
