# ☁️ SHARK v18 - Deploy do Chmury (DARMOWY)

## 🎯 Najlepsza Opcja: Render.com + MongoDB Atlas

**Koszt: 0 zł/miesiąc** 💰

---

## 📋 KROK 1: Przygotowanie MongoDB Atlas (Baza Danych)

### 1.1 Załóż Konto MongoDB Atlas

1. Wejdź na: https://www.mongodb.com/cloud/atlas/register
2. Zarejestruj się (email + hasło)
3. Wybierz **FREE** plan (M0 Sandbox)
4. Wybierz region: **AWS / Frankfurt** (najbliżej Polski)
5. Nazwij cluster: `shark-cluster`
6. Kliknij **Create**

### 1.2 Skonfiguruj Dostęp

1. **Database Access** → **Add New Database User**
   - Username: `shark_user`
   - Password: `[wygeneruj silne hasło]`
   - Role: **Read and write to any database**
   - Kliknij **Add User**

2. **Network Access** → **Add IP Address**
   - Kliknij **Allow Access from Anywhere** (0.0.0.0/0)
   - Kliknij **Confirm**

### 1.3 Pobierz Connection String

1. **Database** → **Connect** → **Connect your application**
2. Skopiuj connection string:
   ```
   mongodb+srv://shark_user:<password>@shark-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
3. Zamień `<password>` na swoje hasło
4. **Zapisz ten string!** Będzie potrzebny później

---

## 📋 KROK 2: Modyfikacja Kodu dla MongoDB

### 2.1 Zainstaluj PyMongo

```bash
pip install pymongo dnspython
```

### 2.2 Zaktualizuj requirements.txt

Dodaj do pliku `requirements.txt`:
```
flask==3.0.0
flask-cors==4.0.0
flask-limiter==3.5.0
qrcode==7.4.2
pillow==10.1.0
pymongo==4.6.0
dnspython==2.4.2
gunicorn==21.2.0
```

### 2.3 Utwórz plik `shark_v18_cloud.py`

```python
import json
import logging
import os
import socket
import threading
import webbrowser
import re
from collections import deque
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# --- KONFIGURACJA MONGODB ---
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
MONGODB_DB = os.environ.get('MONGODB_DB', 'shark_db')

# Połączenie z MongoDB
try:
    mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    mongo_client.admin.command('ping')
    db = mongo_client[MONGODB_DB]
    brain_collection = db['brain']
    logs_collection = db['logs']
    logger.info("✅ MongoDB connected successfully")
except ConnectionFailure as e:
    logger.error(f"❌ MongoDB connection failed: {e}")
    db = None

# --- RESZTA KODU JAK W shark_v18.py ---
# (skopiuj cały kod z shark_v18.py)

# --- ZMIEŃ FUNKCJE load_data() i save_brain() ---

def load_data():
    """Load brain data from MongoDB."""
    global BRAIN, EXTERNAL_DB
    try:
        if db is not None:
            brain_data = brain_collection.find_one({'_id': 'brain_v18'})
            if brain_data:
                BRAIN = brain_data.get('data', {})
                logger.info(f"Brain loaded from MongoDB: {len(BRAIN)} signatures")
            else:
                BRAIN = {}
                logger.info("No brain data in MongoDB, starting fresh")
        else:
            BRAIN = {}
            logger.warning("MongoDB not available, using in-memory storage")
    except Exception as e:
        logger.error(f"Error loading brain from MongoDB: {e}")
        BRAIN = {}

    EXTERNAL_DB = {**STATIC_IDENTIFIERS, **ANDROID_IDENTIFIERS}

def save_brain():
    """Save brain data to MongoDB."""
    try:
        if db is not None:
            brain_collection.update_one(
                {'_id': 'brain_v18'},
                {'$set': {'data': BRAIN, 'updated_at': datetime.utcnow()}},
                upsert=True
            )
            logger.info(f"Brain saved to MongoDB: {len(BRAIN)} signatures")
        else:
            logger.warning("MongoDB not available, brain not saved")
    except Exception as e:
        logger.error(f"Error saving brain to MongoDB: {e}")

# --- DODAJ LOGGING DO MONGODB ---

def log_to_mongodb(event_type, data):
    """Log events to MongoDB."""
    try:
        if db is not None:
            logs_collection.insert_one({
                'timestamp': datetime.utcnow(),
                'type': event_type,
                'data': data
            })
    except Exception as e:
        logger.error(f"Error logging to MongoDB: {e}")

# --- ZMIEŃ app.run() NA KOŃCU ---

if __name__ == '__main__':
    load_data()

    # Dla Render.com - użyj PORT z environment
    port = int(os.environ.get('PORT', 5000))

    print(f"\n{'='*60}")
    print(f"SHARK v18 CLOUD | Port: {port}")
    print(f"Brain signatures: {len(BRAIN)}")
    print(f"MongoDB: {'✅ Connected' if db else '❌ Disconnected'}")
    print(f"{'='*60}\n")

    # Produkcja - bez SSL (Render zapewnia HTTPS)
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )
```

---

## 📋 KROK 3: Deploy na Render.com

### 3.1 Przygotuj Repozytorium Git

```bash
cd C:\temo\install_shark\SHARK_v18_RELEASE

# Inicjalizuj Git
git init

# Utwórz .gitignore
echo "__pycache__/" > .gitignore
echo "*.pyc" >> .gitignore
echo "venv/" >> .gitignore
echo "shark_brain_v18.json" >> .gitignore

# Dodaj pliki
git add .
git commit -m "Initial commit - SHARK v18"
```

### 3.2 Wypchnij na GitHub

1. Wejdź na: https://github.com/new
2. Nazwa: `shark-v18`
3. **Public** lub **Private** (wybierz)
4. Kliknij **Create repository**

```bash
# Dodaj remote
git remote add origin https://github.com/TWOJ_USERNAME/shark-v18.git

# Wypchnij
git branch -M main
git push -u origin main
```

### 3.3 Deploy na Render

1. Wejdź na: https://render.com/
2. Zarejestruj się (GitHub login)
3. Kliknij **New +** → **Web Service**
4. Połącz z GitHub → Wybierz `shark-v18`
5. Konfiguracja:
   - **Name**: `shark-v18`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn shark_v18_cloud:app`
   - **Plan**: **Free**

6. **Environment Variables** (dodaj):
   ```
   MONGODB_URI = mongodb+srv://shark_user:TWOJE_HASLO@shark-cluster.xxxxx.mongodb.net/
   MONGODB_DB = shark_db
   ```

7. Kliknij **Create Web Service**

### 3.4 Czekaj na Deploy

- Render automatycznie zbuduje i uruchomi aplikację
- Po ~5 minutach zobaczysz: **Live** ✅
- Twój URL: `https://shark-v18.onrender.com`

---

## 📋 KROK 4: Testowanie

### 4.1 Otwórz w Przeglądarce

```
https://shark-v18.onrender.com
```

### 4.2 Przetestuj Skanowanie

1. Otwórz na telefonie
2. Kliknij "Rozpocznij Skanowanie"
3. Sprawdź czy działa

### 4.3 Sprawdź MongoDB

1. MongoDB Atlas → **Browse Collections**
2. Powinieneś zobaczyć:
   - `brain` collection (dane AI)
   - `logs` collection (logi)

---

## 🎯 ALTERNATYWNE OPCJE

### Opcja 2: Railway.app

**Zalety:**
- Nie usypia
- $5 kredytu/miesiąc
- Prostsza konfiguracja

**Kroki:**
1. https://railway.app/
2. **New Project** → **Deploy from GitHub**
3. Wybierz repo
4. Dodaj **MongoDB** plugin
5. Deploy!

**Koszt:** ~$2-3/miesiąc (po wykorzystaniu kredytu)

---

### Opcja 3: Heroku (Płatna od 2022)

**Koszt:** $7/miesiąc (Eco Dyno)

**Kroki:**
1. https://heroku.com/
2. Utwórz `Procfile`:
   ```
   web: gunicorn shark_v18_cloud:app
   ```
3. Deploy przez Git
4. Dodaj MongoDB Atlas addon

---

### Opcja 4: PythonAnywhere (Bez MongoDB)

**Darmowy plan:**
- Bez MongoDB
- Tylko JSON file storage
- Limit: 100k requests/day

**Kroki:**
1. https://www.pythonanywhere.com/
2. Upload plików
3. Skonfiguruj WSGI
4. Gotowe!

---

## 💰 Porównanie Kosztów

| Platforma | Koszt/miesiąc | MongoDB | HTTPS | Usypianie |
|-----------|---------------|---------|-------|-----------|
| **Render.com** | **0 zł** ✅ | Atlas (0 zł) | ✅ | Tak (15 min) |
| **Railway.app** | 0-10 zł | Wbudowane | ✅ | Nie |
| **Heroku** | ~30 zł | Atlas (0 zł) | ✅ | Nie |
| **PythonAnywhere** | 0 zł | ❌ | ✅ | Nie |

---

## 🔧 Dodatkowe Pliki dla Deploy

### Procfile (dla Heroku/Railway)
```
web: gunicorn shark_v18_cloud:app
```

### runtime.txt (opcjonalnie)
```
python-3.10.12
```

### .env (lokalnie - NIE commituj!)
```
MONGODB_URI=mongodb+srv://shark_user:haslo@shark-cluster.xxxxx.mongodb.net/
MONGODB_DB=shark_db
PORT=5000
```

---

## 🆘 Troubleshooting

### Problem: "Application failed to start"

**Rozwiązanie:**
1. Sprawdź logi w Render
2. Upewnij się że `gunicorn` jest w requirements.txt
3. Sprawdź czy `shark_v18_cloud.py` istnieje

### Problem: "MongoDB connection timeout"

**Rozwiązanie:**
1. Sprawdź czy IP 0.0.0.0/0 jest dozwolone w MongoDB Atlas
2. Sprawdź connection string (hasło, nazwa clustera)
3. Sprawdź zmienną środowiskową `MONGODB_URI`

### Problem: "App keeps sleeping"

**Rozwiązanie:**
1. To normalne dla darmowego planu Render
2. Użyj Railway.app (nie usypia)
3. Lub upgrade do płatnego planu ($7/miesiąc)

---

## 📊 Monitoring

### Render Dashboard
- Logi w czasie rzeczywistym
- Metryki CPU/RAM
- Request count

### MongoDB Atlas
- Database size
- Operations/second
- Slow queries

---

## ✅ Checklist Deploy

- [ ] MongoDB Atlas skonfigurowane
- [ ] Connection string zapisany
- [ ] requirements.txt zaktualizowany
- [ ] shark_v18_cloud.py utworzony
- [ ] Git repo utworzone
- [ ] Kod wypchnięty na GitHub
- [ ] Render.com skonfigurowane
- [ ] Environment variables dodane
- [ ] Deploy zakończony sukcesem
- [ ] Aplikacja działa w przeglądarce
- [ ] MongoDB zapisuje dane

---

## 🎉 Gotowe!

Twój SHARK v18 działa w chmurze **ZA DARMO**! 🦈☁️

**URL:** https://shark-v18.onrender.com

**Udostępnij link** klientom i zacznij skanować telefony z dowolnego miejsca na świecie! 🌍📱

---

**Czas setup:** ~30 minut
**Koszt:** 0 zł/miesiąc
**Trudność:** ⭐⭐☆☆☆ (średnia)
