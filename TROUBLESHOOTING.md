# SHARK v18 - Rozwiązywanie Problemów (Troubleshooting)

## 🔧 Najczęstsze Problemy i Rozwiązania

---

## 1. 📱 Telefon Nie Rozpoznany

### Objawy:
- Algorytm pokazuje niską pewność (< 60%)
- Brak sugestii AI
- Model pokazuje "Nieznany"

### Rozwiązanie:

#### Krok 1: Sprawdź User-Agent
1. Otwórz DevTools (F12)
2. Przejdź do Console
3. Wpisz: `navigator.userAgent`
4. Skopiuj wynik

**Przykład:**
```
Mozilla/5.0 (Linux; Android 14; SM-S911B) AppleWebKit/537.36
(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36
```

#### Krok 2: Użyj "Zapisz i Naucz AI"
1. Kliknij przycisk **"Skanuj Ponownie"**
2. Przewiń w dół do sekcji **"Nie rozpoznano? Naucz AI!"**
3. Wpisz nazwę modelu (np. "Samsung Galaxy S24")
4. Kliknij **"Zapisz i Naucz AI"**

#### Krok 3: Dodaj do ANDROID_IDENTIFIERS (dla deweloperów)

**Jeśli telefon ma unikalny identyfikator w User-Agent:**

1. Otwórz plik: `app/models/identifiers.py`
2. Znajdź sekcję `ANDROID_IDENTIFIERS`
3. Dodaj nowy wpis:

```python
ANDROID_IDENTIFIERS = {
    # ... istniejące wpisy ...

    # Samsung Galaxy S24
    "SM-S921B": "Samsung Galaxy S24",
    "SM-S926B": "Samsung Galaxy S24 Plus",
    "SM-S928B": "Samsung Galaxy S24 Ultra",

    # Twój nowy telefon
    "IDENTYFIKATOR": "Nazwa Modelu",
}
```

4. Zapisz plik
5. Zrestartuj aplikację: `python main.py`

**Jak znaleźć identyfikator?**
- User-Agent: `Mozilla/5.0 (Linux; Android 14; **SM-S911B**) ...`
- Identyfikator to: `SM-S911B`

---

## 2. 🔲 QR Code Się Nie Wyświetla

### Objawy:
- Brak QR kodu w panelu administracyjnym
- Błąd: `ModuleNotFoundError: No module named 'qrcode'`
- Puste miejsce gdzie powinien być QR kod

### Rozwiązanie:

#### Instalacja biblioteki qrcode

**Windows:**
```bash
pip install qrcode[pil]
```

**Linux/Mac:**
```bash
pip3 install qrcode[pil]
```

**Weryfikacja instalacji:**
```bash
python -c "import qrcode; print('QR Code installed:', qrcode.__version__)"
```

**Jeśli nadal nie działa, zainstaluj Pillow:**
```bash
pip install Pillow
```

#### Restart aplikacji:
```bash
cd C:/temo/install_shark/SHARK_v18_RELEASE
python main.py
```

---

## 3. ⚙️ Algorytm Pokazuje 0%

### Objawy:
- "⚙️ ALGORYTM: 0%"
- Sugestie AI pokazują 0%

### Rozwiązanie:

**To zostało naprawione w v18.27!**

1. Upewnij się że masz najnowszą wersję:
```bash
git pull origin master
```

2. Wyczyść cache przeglądarki:
- **Windows:** `Ctrl + Shift + R`
- **Mac:** `Cmd + Shift + R`

3. Odśwież stronę

**Jeśli nadal pokazuje 0%:**
- Sprawdź czy Render wdrożył zmiany (poczekaj 2-3 minuty)
- Sprawdź Console (F12) czy są błędy JavaScript

---

## 4. 🗄️ MongoDB Nie Łączy Się

### Objawy:
- Błąd: `MongoDB connection failed`
- Aplikacja nie startuje
- Brak danych w bazie

### Rozwiązanie:

#### Sprawdź plik `.env`:
```bash
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DB=shark_v18
```

#### Sprawdź połączenie:
```bash
python -c "from pymongo import MongoClient; client = MongoClient('YOUR_URI'); print('Connected:', client.server_info())"
```

#### Typowe błędy:

**1. Błędne hasło:**
- Sprawdź czy hasło nie zawiera znaków specjalnych
- Jeśli tak, zakoduj je: `%40` zamiast `@`, `%23` zamiast `#`

**2. IP nie dodane do whitelist:**
- Wejdź na MongoDB Atlas
- Network Access → Add IP Address → Allow Access from Anywhere (0.0.0.0/0)

**3. Brak uprawnień:**
- Database Access → Sprawdź czy user ma rolę `readWrite`

---

## 5. 🚀 Render Deploy Nie Działa

### Objawy:
- Deploy failed
- Aplikacja nie startuje na Render
- 502 Bad Gateway

### Rozwiązanie:

#### Sprawdź logi Render:
1. Wejdź na Render Dashboard
2. Kliknij swoją aplikację
3. Przejdź do "Logs"
4. Szukaj błędów

#### Typowe problemy:

**1. Brak requirements.txt:**
```bash
# Wygeneruj requirements.txt
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Add requirements.txt"
git push origin master
```

**2. Błędny start command:**
- Render → Settings → Start Command
- Powinno być: `gunicorn main:app`

**3. Brak zmiennych środowiskowych:**
- Render → Environment
- Dodaj: `MONGODB_URI`, `MONGODB_DB`

**4. Port binding:**
- Render automatycznie ustawia `PORT`
- Upewnij się że aplikacja używa `os.environ.get('PORT', 5000)`

---

## 6. 🧠 Brain Nie Uczy Się

### Objawy:
- Kliknięcie "Zapisz i Naucz AI" nie działa
- Brak nowych sygnatur w bazie
- Błąd 500 przy zapisie

### Rozwiązanie:

#### Sprawdź logi:
```bash
# Lokalnie
python main.py
# Sprawdź output w konsoli

# Render
# Dashboard → Logs
```

#### Sprawdź MongoDB:
```bash
# Sprawdź czy kolekcja brain_v18 istnieje
# MongoDB Atlas → Browse Collections → shark_v18 → brain_v18
```

#### Sprawdź uprawnienia:
```python
# Test zapisu
from app.database import save_brain_signature
result = save_brain_signature("test_sig", {"test": "data"})
print("Save result:", result)
```

---

## 7. 📊 External DB Nie Ładuje Się

### Objawy:
- "External DB: 0 models"
- Brak sugestii z bazy Matomo
- Długi czas ładowania

### Rozwiązanie:

#### Import bazy Matomo:
```bash
cd C:/temo/install_shark/SHARK_v18_RELEASE
python setup_database.py
```

#### Sprawdź czy plik istnieje:
```bash
# Powinien być plik: matomo_devices.json
ls -la matomo_devices.json
```

#### Ręczny import:
```python
from app.database import init_mongodb
init_mongodb()
# Sprawdź logi
```

---

## 8. 🎨 Frontend Nie Ładuje Się

### Objawy:
- Biała strona
- Błędy JavaScript w Console
- Brak stylów CSS

### Rozwiązanie:

#### Sprawdź Console (F12):
- Szukaj błędów JavaScript
- Sprawdź czy wszystkie pliki się załadowały

#### Wyczyść cache:
```bash
# Chrome/Edge
Ctrl + Shift + Delete → Clear browsing data

# Firefox
Ctrl + Shift + Delete → Clear Recent History
```

#### Sprawdź ścieżki:
```html
<!-- templates/index.html -->
<!-- Upewnij się że ścieżki są poprawne -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
<script src="{{ url_for('static', filename='js/scanner.js') }}"></script>
```

---

## 9. 🔒 Rate Limiter Blokuje Requesty

### Objawy:
- Błąd 429: Too Many Requests
- "Rate limit exceeded"
- Nie można skanować

### Rozwiązanie:

#### Zwiększ limity (development):
```python
# main.py
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"],  # Zwiększone limity
    storage_uri="memory://"
)
```

#### Wyłącz rate limiting (tylko development!):
```python
# main.py
# Zakomentuj dekorator @limiter.limit
@app.route('/api/check_brain', methods=['POST'])
# @limiter.limit("30 per minute")  # Wyłączone
def check_brain():
    # ...
```

#### Poczekaj:
- Limity resetują się co godzinę
- Lub zrestartuj aplikację (memory storage)

---

## 10. 📱 Telefon Wykrywa Się Jako Laptop

### Objawy:
- iPhone wykrywa się jako "Nieznany"
- Rozdzielczość 1520x695 (to laptop!)
- DPR 1.25x (to monitor!)

### Rozwiązanie:

**To NIE jest bug - testujesz na komputerze!**

#### Jak przetestować na telefonie:

**Opcja 1: Lokalnie (ta sama sieć WiFi)**
```bash
# Uruchom aplikację
python main.py

# Sprawdź IP komputera
ipconfig  # Windows
ifconfig  # Linux/Mac

# Na telefonie otwórz:
http://192.168.1.XXX:5000
```

**Opcja 2: Online (Render)**
```bash
# Otwórz na telefonie:
https://twoja-aplikacja.onrender.com
```

**Opcja 3: Symulacja w przeglądarce**
```bash
# Chrome DevTools (F12)
# Ctrl + Shift + M (Toggle device toolbar)
# Wybierz: iPhone 11, Samsung Galaxy S24, etc.
```

---

## 11. 🔄 Zmiany Nie Wdrażają Się

### Objawy:
- Zmiany w kodzie nie są widoczne
- Stara wersja nadal działa
- Cache przeglądarki

### Rozwiązanie:

#### Lokalnie:
```bash
# Zrestartuj aplikację
Ctrl + C  # Zatrzymaj
python main.py  # Uruchom ponownie
```

#### Render:
```bash
# Push do GitHub
git add .
git commit -m "Your changes"
git push origin master

# Poczekaj 2-3 minuty na auto-deploy
# Sprawdź: Render Dashboard → Logs
```

#### Wyczyść cache:
```bash
# Hard refresh
Ctrl + Shift + R  # Windows
Cmd + Shift + R   # Mac
```

---

## 12. 💾 Brak Miejsca na Dysku (Render)

### Objawy:
- Deploy failed: "No space left on device"
- Aplikacja crashuje
- Brak logów

### Rozwiązanie:

#### Wyczyść cache Render:
```bash
# Render Dashboard → Settings → Clear build cache
```

#### Zmniejsz rozmiar aplikacji:
```bash
# Usuń niepotrzebne pliki
rm -rf __pycache__
rm -rf .git/objects/pack/*.pack  # Stare commity
```

#### Użyj .gitignore:
```bash
# .gitignore
__pycache__/
*.pyc
*.pyo
*.log
.env
node_modules/
```

---

## 📞 Kontakt i Wsparcie

### Zgłaszanie Błędów:
1. Otwórz issue na GitHub
2. Dołącz:
   - Opis problemu
   - Kroki do reprodukcji
   - Logi (Console + Server)
   - Screenshot
   - Wersja aplikacji (sprawdź `/version`)

### Przydatne Komendy:

```bash
# Sprawdź wersję
curl http://localhost:5000/version

# Sprawdź logi
tail -f logs/shark.log

# Sprawdź status MongoDB
python -c "from app.database import init_mongodb; init_mongodb()"

# Sprawdź Brain
python -c "from app.config import BRAIN; print(len(BRAIN), 'signatures')"

# Sprawdź External DB
python -c "from app.config import EXTERNAL_DB; print(len(EXTERNAL_DB), 'models')"
```

---

## 🔍 Debug Mode

### Włącz tryb debug (tylko development!):

```python
# main.py
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=True  # ✅ Włącz debug
    )
```

**Uwaga:** NIE używaj `debug=True` w produkcji (Render)!

---

## 📚 Dodatkowe Zasoby

- **Dokumentacja:** `REFACTORING_NOTES.md`
- **Changelog:** `CHANGELOG_v18.*.md`
- **Architecture:** `ARCHITECTURE_IMPROVEMENTS.md`
- **Quick Start:** `QUICK_START.md`

---

**Ostatnia aktualizacja:** 2026-02-02 (v18.27)
