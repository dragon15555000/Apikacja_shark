# SHARK v18

```http
POST /api/check_brain
Content-Type: application/json

{"w":390,"h":844,"hz":60,"dpr":3,"gpu":"Apple GPU","userAgent":"Mozilla/5.0 (iPhone; ...)"}
```

Odpowiedź: model telefonu, pewność, źródło trafienia (`UA_EXACT`, `BRAIN`, `HEURISTIC`, …), kody szkła i etui z magazynu.

Sklep potrzebował rozpoznać urządzenie klienta w przeglądarce (bez instalacji apki) i od razu podać właściwe kody akcesoriów. Stąd ten serwis — fingerprint z ekranu, GPU, Hz, DPR i User-Agent.

Kolejność prób: najpierw UA (np. `iPhone17,1`, `SM-S928B`) — jeśli pasuje, koniec, 100%. Potem słownik BRAIN (nauczone sygnatury, do 10k wpisów, max 5 modeli na sygnaturę, LFU przy przepełnieniu). Na końcu heurystyka punktowa po rozdzielczości / DPR / GPU; auto-wybór gdy lider ≥ 90 pkt i drugi < 60.

Zapis: MongoDB `$set` w produkcji, albo plik JSON + `.tmp` + `os.replace` lokalnie — żeby gunicorn z wieloma workerami nie rozwalił pliku w połowie zapisu.

iPhone 11–17 (27 modeli), Samsung S/A/Z, Pixel 5–8 Pro, Xiaomi, OnePlus, Huawei — łącznie 50+ Androidów w bazie.

Python 3.13, Flask 3.1. `MONGODB_URI` opcjonalne — bez niego jedzie na JSON. Rate limit: 30/min na `check_brain`, 10/min na `learn`. Testy w `tests/`.

```bash
pip install -r requirements.txt
cp .env.example .env
python shark_v18_cloud.py
```

Produkcja: `gunicorn shark_v18_cloud:app`. Więcej o Render/Atlas: `DEPLOY_CLOUD.md`.

`POST /api/learn` — dopisuje sygnaturę (ograniczone). `/admin` — panel, wymaga Mongo.

Proprietary.
