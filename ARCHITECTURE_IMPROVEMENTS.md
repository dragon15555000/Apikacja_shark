# SHARK v18.25 - Architecture Improvements Plan

## 🎯 Zidentyfikowane Ryzyka

### 1. ⚠️ Rate Limiter w Pamięci (KRYTYCZNE)
**Problem:**
```python
# main.py linia 32-37
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # ❌ PROBLEM!
)
```

**Ryzyko:**
- `storage_uri="memory://"` działa tylko w pojedynczym procesie
- Przy skalowaniu (gunicorn z wieloma workerami, Render auto-scaling) każdy proces ma własny licznik
- Użytkownik może obejść limit wysyłając requesty do różnych workerów
- Brak współdzielonego stanu między procesami

**Rozwiązanie:**
```python
# Opcja 1: Redis (ZALECANE dla produkcji)
storage_uri="redis://localhost:6379"

# Opcja 2: Memcached
storage_uri="memcached://localhost:11211"

# Opcja 3: MongoDB (już mamy!)
storage_uri="mongodb://user:pass@host:27017/db"
```

**Implementacja:**
- Dodać Redis do requirements.txt
- Skonfigurować Redis URI w .env
- Fallback do memory:// w trybie development
- Dodać health check dla Redis

---

### 2. ⚠️ Brak Separacji Frontend/Backend (ŚREDNIE)
**Problem:**
```python
# Obecnie: templates/index.html zawiera 231 linii JavaScript
# Wszystko w jednym pliku - HTML + CSS + JavaScript
```

**Ryzyko:**
- Trudny rozwój UI (brak hot-reload, brak narzędzi deweloperskich)
- Niemożliwe testy jednostkowe JavaScript
- Brak możliwości użycia nowoczesnych frameworków (React, Vue)
- Trudny refactoring i utrzymanie kodu
- Brak możliwości CDN dla statycznych zasobów

**Rozwiązanie:**
```
SHARK_v18_RELEASE/
├── static/
│   ├── css/
│   │   └── main.css          # Wydzielone style
│   ├── js/
│   │   ├── scanner.js        # Logika skanowania
│   │   ├── ui.js             # Logika UI
│   │   └── api.js            # Komunikacja z API
│   └── img/
│       └── logo.png
├── templates/
│   └── index.html            # Tylko struktura HTML
```

**Implementacja:**
- Przenieść CSS do `static/css/main.css`
- Przenieść JavaScript do modułów w `static/js/`
- Użyć Flask `url_for('static', filename='...')` dla zasobów
- Dodać możliwość budowania z webpack/vite w przyszłości

---

### 3. ⚠️ Ryzyko Współbieżności przy Zapisie BRAIN (KRYTYCZNE)
**Problem:**
```python
# app/database.py linia 162-181
def save_brain():
    """Save brain data to MongoDB or JSON file."""
    import app.config as config

    try:
        if USE_MONGODB:
            brain_collection.update_one(
                {'_id': 'brain_v18'},
                {'$set': {'data': config.BRAIN, 'updated_at': datetime.utcnow()}},
                upsert=True
            )
            # ❌ PROBLEM: Nadpisuje cały BRAIN!
```

**Ryzyko:**
- Przy wielu workerach (gunicorn -w 4) każdy proces ma własną kopię `config.BRAIN` w pamięci
- Worker A uczy się modelu X → zapisuje cały BRAIN
- Worker B uczy się modelu Y → zapisuje cały BRAIN (nadpisuje X!)
- **Race condition:** Dane z Worker A mogą zostać utracone
- Brak blokady międzyprocesowej

**Przykład problemu:**
```
T0: Worker A: BRAIN = {"sig1": "iPhone 11"}
T1: Worker B: BRAIN = {"sig1": "iPhone 11"}
T2: Worker A: Uczy się "sig2": "Samsung S24" → BRAIN = {"sig1": "iPhone 11", "sig2": "Samsung S24"}
T3: Worker B: Uczy się "sig3": "Pixel 8" → BRAIN = {"sig1": "iPhone 11", "sig3": "Pixel 8"}
T4: Worker A: Zapisuje do MongoDB → {"sig1": "iPhone 11", "sig2": "Samsung S24"}
T5: Worker B: Zapisuje do MongoDB → {"sig1": "iPhone 11", "sig3": "Pixel 8"}
WYNIK: sig2 UTRACONE! ❌
```

**Rozwiązanie:**
```python
# Opcja 1: Atomiczne operacje MongoDB (ZALECANE)
def save_brain_signature(fingerprint, model_data):
    """Atomicznie dodaj pojedynczą sygnaturę do BRAIN"""
    brain_collection.update_one(
        {'_id': 'brain_v18'},
        {
            '$set': {
                f'data.{fingerprint}': model_data,
                'updated_at': datetime.utcnow()
            }
        },
        upsert=True
    )
    # ✅ Atomiczne - bezpieczne dla wielu workerów!

# Opcja 2: Distributed Lock (Redis)
from redis import Redis
from redis.lock import Lock

redis_client = Redis()
lock = Lock(redis_client, "brain_write_lock", timeout=5)

with lock:
    # Zapisz BRAIN
    save_brain()

# Opcja 3: MongoDB Transactions (wymaga replica set)
with client.start_session() as session:
    with session.start_transaction():
        # Operacje na BRAIN
        brain_collection.update_one(...)
```

---

## 🔧 Plan Implementacji

### Faza 1: Rate Limiter (v18.25)
- [ ] Dodać `redis` do requirements.txt
- [ ] Dodać `REDIS_URI` do .env i config.py
- [ ] Zmodyfikować main.py - użyć Redis storage
- [ ] Dodać fallback do memory:// w development
- [ ] Dodać health check endpoint `/health/redis`
- [ ] Przetestować z wieloma workerami

### Faza 2: Separacja Frontend (v18.26)
- [ ] Utworzyć strukturę `static/css/`, `static/js/`
- [ ] Wydzielić CSS do `static/css/main.css`
- [ ] Wydzielić JavaScript do modułów:
  - `scanner.js` - logika skanowania
  - `ui.js` - manipulacja DOM
  - `api.js` - komunikacja z backend
- [ ] Zaktualizować `templates/index.html`
- [ ] Dodać minifikację w produkcji
- [ ] Przetestować wszystkie funkcje

### Faza 3: Atomiczne Zapisy BRAIN (v18.27)
- [ ] Zmienić `save_brain()` na `save_brain_signature(fp, data)`
- [ ] Użyć MongoDB `$set` z kluczem `data.{fingerprint}`
- [ ] Zaktualizować endpoint `/api/learn`
- [ ] Dodać `load_brain_signature(fp)` dla odczytu
- [ ] Usunąć globalny `config.BRAIN` (opcjonalnie)
- [ ] Przetestować z wieloma workerami (gunicorn -w 4)
- [ ] Dodać testy współbieżności

---

## 📊 Porównanie: Przed vs Po

### Rate Limiter
| Aspekt | Przed (memory://) | Po (Redis) |
|--------|------------------|------------|
| Skalowanie | ❌ Nie działa | ✅ Działa |
| Wieloprocesowość | ❌ Każdy proces osobno | ✅ Współdzielony stan |
| Persistence | ❌ Ginie przy restarcie | ✅ Zachowane w Redis |
| Performance | ✅ Szybkie | ✅ Szybkie (~1ms) |

### Frontend/Backend
| Aspekt | Przed | Po |
|--------|-------|-----|
| Struktura | ❌ Wszystko w HTML | ✅ Separacja plików |
| Rozwój | ❌ Trudny | ✅ Łatwy |
| Testy | ❌ Niemożliwe | ✅ Możliwe |
| CDN | ❌ Nie | ✅ Tak |
| Hot-reload | ❌ Nie | ✅ Tak |

### BRAIN Concurrency
| Aspekt | Przed | Po |
|--------|-------|-----|
| Race conditions | ❌ Możliwe | ✅ Niemożliwe |
| Utrata danych | ❌ Możliwa | ✅ Niemożliwa |
| Wieloprocesowość | ❌ Niebezpieczne | ✅ Bezpieczne |
| Atomowość | ❌ Nie | ✅ Tak |

---

## 🚀 Dodatkowe Ulepszenia (Opcjonalne)

### 4. Monitoring i Observability
```python
# Dodać metryki Prometheus
from prometheus_flask_exporter import PrometheusMetrics
metrics = PrometheusMetrics(app)

# Metryki:
# - shark_detections_total
# - shark_learning_total
# - shark_brain_size
# - shark_api_latency
```

### 5. Caching
```python
# Cache dla External DB (14,740 modeli)
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@cache.memoize(timeout=3600)
def get_external_db():
    return load_external_db()
```

### 6. API Versioning
```python
# /api/v1/check_brain
# /api/v2/check_brain (nowa wersja)
# Backward compatibility
```

### 7. WebSocket dla Real-time Updates
```python
# Socket.IO dla live updates w admin panelu
from flask_socketio import SocketIO
socketio = SocketIO(app)

@socketio.on('scan')
def handle_scan(data):
    # Real-time progress updates
    emit('progress', {'status': 'scanning'})
```

---

## 📝 Notatki

### Priorytet Implementacji
1. **KRYTYCZNE:** BRAIN Concurrency (utrata danych!)
2. **WYSOKIE:** Rate Limiter (bezpieczeństwo)
3. **ŚREDNIE:** Frontend Separation (developer experience)

### Kompatybilność Wsteczna
- Wszystkie zmiany będą backward compatible
- Stare API endpoints będą działać
- Migracja danych automatyczna

### Testowanie
- Unit testy dla nowych funkcji
- Integration testy dla MongoDB atomics
- Load testy dla Rate Limiter (Redis)
- Concurrency testy dla BRAIN (pytest-xdist)

---

**Autor:** AI Assistant
**Data:** 2026-02-01
**Wersja:** v18.25 Planning Document
