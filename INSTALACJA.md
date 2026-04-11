# Instalacja SHARK v18

## Wymagania

- Python 3.10+ (zalecane 3.13)
- pip
- Dostęp do sieci (lokalnej lub internet dla MongoDB)

---

## Instalacja lokalna

### 1. Zainstaluj zależności

```bash
pip install -r requirements.txt
```

### 2. Skonfiguruj zmienne środowiskowe (opcjonalnie)

```bash
cp .env.example .env
# Edytuj .env i uzupełnij MONGODB_URI jeśli używasz MongoDB
```

Bez `.env` aplikacja działa w trybie JSON (brain zapisywany w `shark_brain_v18.json`).

### 3. Zainicjalizuj bazę urządzeń (opcjonalnie, zalecane)

Pobiera 14 000+ modeli z Matomo Device Detector do pliku `shark_external_db.json`:

```bash
python setup_database.py
```

Przy ponownym uruchomieniu skrypt zapyta, czy zaktualizować bazę z sieci.

### 4. Uruchom aplikację

```bash
python shark_v18_cloud.py
```

Aplikacja startuje na `http://0.0.0.0:5000`.

---

## Konfiguracja MongoDB

MongoDB jest zalecane dla środowiska produkcyjnego (panel admin, logi detekcji).

### 1. Utwórz klaster (MongoDB Atlas – darmowy tier M0)

1. Zarejestruj się na [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas/register)
2. Utwórz cluster (M0 Sandbox, region Frankfurt)
3. **Database Access** → dodaj użytkownika z rolą *Read and write*
4. **Network Access** → dodaj `0.0.0.0/0` (dostęp z dowolnego IP)
5. **Connect** → skopiuj connection string (format: `mongodb+srv://user:pass@cluster.mongodb.net/`)

### 2. Ustaw zmienne środowiskowe

W pliku `.env`:
```env
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=shark_db
```

### 3. (Opcjonalnie) Importuj brain z JSON do MongoDB

Jeśli masz istniejącą bazę w `shark_brain_v18.json`:

```bash
python migrate_to_mongodb.py
```

---

## Rozwiązywanie problemów

### `python` nie jest rozpoznawany

```bash
# Użyj python3 lub py (Windows)
python3 shark_v18_cloud.py
py shark_v18_cloud.py
```

### Port 5000 zajęty

Ustaw zmienną środowiskową przed uruchomieniem:

```bash
PORT=5001 python shark_v18_cloud.py
```

### Błąd instalacji pakietów

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Lub użyj środowiska wirtualnego:

```bash
python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### `ModuleNotFoundError`

Upewnij się, że instalujesz w tym samym Pythonie, którym uruchamiasz aplikację:

```bash
python -m pip install -r requirements.txt
python shark_v18_cloud.py
```

---

## Weryfikacja instalacji

```bash
# Uruchom testy jednostkowe
pytest tests/ -v

# Sprawdź endpoint
curl http://localhost:5000/api/check_brain \
  -H "Content-Type: application/json" \
  -d '{"w":390,"h":844,"hz":60,"dpr":3,"gpu":"Apple GPU","ram":-1,"cores":6,"canvasHash":"test","userAgent":"Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)","dprVerified":true,"isZoomed":false}'
```

---

## Dalsze kroki

- [QUICK_START.md](QUICK_START.md) – pierwsze kroki z interfejsem
- [DEPLOY_CLOUD.md](DEPLOY_CLOUD.md) – wdrożenie na Render / Heroku
- [INSTRUKCJA_OBSLUGI.md](INSTRUKCJA_OBSLUGI.md) – obsługa systemu
