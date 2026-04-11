# 🦈 SHARK v18

System automatycznego rozpoznawania urządzeń mobilnych (iOS i Android) z wykorzystaniem AI i browser fingerprinting. Identyfikuje model telefonu i zwraca kody akcesoriów (szkła ochronne, etui).

**Wersja:** 18.33 · **Python:** 3.13 · **Framework:** Flask

---

## Jak działa

Rozpoznawanie odbywa się w trzech warstwach (kolejność priorytetu):

| Metoda | Źródło | Pewność |
|---|---|---|
| **UA_EXACT** | User-Agent → znany identyfikator w bazie | 100% |
| **AI_FINGERPRINT** | Zapamiętana sygnatura sprzętowa | 85–95% |
| **HEURISTIC** | Ważony scoring wg rozdzielczości / GPU / DPR | 60–80% |

---

## Szybki start

```bash
# 1. Zainstaluj zależności
pip install -r requirements.txt

# 2. Uruchom serwer
python shark_v18_cloud.py

# 3. Otwórz w przeglądarce
http://localhost:5000
```

> Pełna instrukcja instalacji: [INSTALACJA.md](INSTALACJA.md)  
> Wdrożenie na chmurę: [DEPLOY_CLOUD.md](DEPLOY_CLOUD.md)

---

## Struktura projektu

```
/
├── shark_v18_cloud.py      # Główny plik aplikacji (Flask)
├── Procfile                # Gunicorn – produkcja (Heroku/Render)
├── requirements.txt        # Zależności Python
├── runtime.txt             # Python 3.13.4
├── .env.example            # Szablon zmiennych środowiskowych
│
├── app/
│   ├── config.py           # Ustawienia (wersja, DB, logowanie)
│   ├── database.py         # Inicjalizacja BRAIN / EXTERNAL_DB
│   ├── logic.py            # Shim – re-eksportuje app/utils/logic.py
│   ├── models/
│   │   ├── identifiers.py          # STATIC_IDENTIFIERS (iOS) + ANDROID_IDENTIFIERS
│   │   ├── heuristic_db.py         # HEURISTIC_DB – specyfikacje urządzeń
│   │   └── accessory_codes.py      # ACCESSORY_CODES – kody magazynowe
│   ├── routes/
│   │   ├── api_routes.py           # /api/check_brain, /api/learn
│   │   └── admin_routes.py         # /admin, /admin/api/*
│   └── utils/
│       ├── logic.py                # Algorytmy: parse_device_from_ua, find_top_3_matches
│       └── validators.py           # Dekorator @validate_json
│
├── templates/
│   ├── index.html          # Interfejs klienta
│   └── admin.html          # Panel administracyjny
│
├── tests/                  # Testy jednostkowe (pytest)
├── shark_external_db.json  # Zewnętrzna baza 14 000+ modeli
└── _archiwum/              # Pliki historyczne / nieużywane
```

---

## Zmienne środowiskowe

Skopiuj `.env.example` do `.env`:

| Zmienna | Opis | Wymagana |
|---|---|---|
| `MONGODB_URI` | URI do MongoDB Atlas | Zalecana |
| `MONGODB_DB` | Nazwa bazy (domyślnie `shark_db`) | Nie |
| `REDIS_URI` | URI do Redis (rate limiter multi-worker) | Nie |
| `PORT` | Port serwera (domyślnie `5000`) | Nie |

Bez `MONGODB_URI` aplikacja działa w trybie pliku JSON (`shark_brain_v18.json`).

---

## API

### `POST /api/check_brain`
Rozpoznaje urządzenie. Limit: 30 req/min.

**Żądanie:**
```json
{
  "w": 390, "h": 844, "hz": 60, "dpr": 3.0,
  "gpu": "Apple GPU", "ram": -1, "cores": 6,
  "canvasHash": "abc123",
  "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 ...)",
  "dprVerified": true, "isZoomed": false
}
```

**Odpowiedź (znaleziono):**
```json
{
  "found": true,
  "model": "iPhone 15",
  "confidence": 100,
  "source": "UA_EXACT",
  "codes": { "screen": "AP1234", "case": "AP5678" }
}
```

### `POST /api/learn`
Uczy AI nowej sygnatury. Limit: 10 req/min.  
Wymagane te same pola co `/api/check_brain` plus `"model": "Nazwa modelu"`.

### `GET /admin`
Panel administracyjny (wymaga MongoDB).

---

## Obsługiwane urządzenia

**iPhone:** 11–17 Pro Max (wszystkie modele)  
**Samsung:** S20–S25 Ultra, A14–A55, Z Fold 3–6, Z Flip 3–6  
**Google Pixel:** 5–9 Pro Fold, 8a  
**Xiaomi:** Mi 10T Pro – 14 Pro  
**OnePlus:** 8–13 (CPH/LE/IN kody)  
**Huawei/Honor:** P30–P40 Pro  
**Sony Xperia, ASUS ROG, Nothing Phone, Vivo/iQOO, Realme, Motorola**

Łącznie: **90+ modeli** ze 100% pewnością (UA_EXACT).

---

## Dodawanie nowych urządzeń

```python
# 1. app/models/identifiers.py – identyfikator UA
ANDROID_IDENTIFIERS["SM-XXXX"] = "Samsung Galaxy NOWY MODEL"

# 2. app/models/accessory_codes.py – kody magazynowe
ACCESSORY_CODES["Samsung Galaxy NOWY MODEL"] = {"screen": "SA9U1", "case": "SA9U2"}

# 3. app/models/heuristic_db.py – parametry sprzętu (opcjonalnie)
HEURISTIC_DB["Samsung Galaxy NOWY MODEL"] = {"w": 412, "h": 915, "dpr": 3.0, "ram": 8, "hz": 120, "gpu": "adreno 740"}
```

---

## Testy

```bash
pytest tests/ -v
```

---

## Wdrożenie produkcyjne

```bash
gunicorn shark_v18_cloud:app
```

Platformy: Heroku, Render. Szczegóły: [DEPLOY_CLOUD.md](DEPLOY_CLOUD.md).

---

## Bezpieczeństwo

- Rate limiting (Flask-Limiter + opcjonalnie Redis)
- Walidacja wejścia (`@validate_json`, sprawdzanie zakresów)
- Ochrona przed ReDoS (limit UA do 1000 znaków)
- Atomiczne zapisy brain (`.tmp` + `os.replace`)

Szczegóły: [README_SECURITY.md](README_SECURITY.md)

---

*Licencja: Proprietary – Wszelkie prawa zastrzeżone*
