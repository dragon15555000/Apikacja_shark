# 📦 SHARK v18 - Instalacja Bazy Modeli

## 🎯 Cel

SHARK v18 teraz automatycznie importuje **14,000+ modeli telefonów** z Matomo Device Detector, dzięki czemu system startuje z pełną bazą danych zamiast pustej.

---

## 🚀 Metoda 1: Automatyczny Setup (ZALECANE)

### Krok 1: Uruchom Skrypt Setup

```powershell
cd C:\temo\install_shark\SHARK_v18_RELEASE
python setup_database.py
```

### Krok 2: Poczekaj na Import

```
============================================================
🦈 SHARK v18 - Automatyczny Setup Bazy Danych
============================================================

2026-01-30 13:32:19,124 - 🚀 Rozpoczynam import modeli z Matomo Device Detector...
2026-01-30 13:32:19,239 - 📥 Pobieranie danych z Matomo Device Detector...
2026-01-30 13:32:21,390 - 🔄 Przetwarzanie danych Matomo...
2026-01-30 13:32:21,424 - ✅ Import zakończony!
2026-01-30 13:32:21,424 -    • Nowe modele: 14662
2026-01-30 13:32:21,424 -    • Zaktualizowane: 0
2026-01-30 13:32:21,424 -    • Łącznie w bazie: 14742

============================================================
✅ SETUP ZAKOŃCZONY POMYŚLNIE!
============================================================
```

### Krok 3: Uruchom Aplikację

```powershell
python shark_v18_cloud.py
```

Aplikacja automatycznie wczyta bazę z pliku `shark_external_db.json`:

```
2026-01-30 13:32:40,196 - 📁 Using JSON file storage (no MongoDB)
2026-01-30 13:32:40,203 - ✅ External DB loaded: 14742 models
```

---

## 🌐 Metoda 2: Import przez Panel Admin (Render/Cloud)

### Krok 1: Wejdź na Panel Admin

```
https://twoja-domena.onrender.com/admin
```

### Krok 2: Kliknij "Importuj Modele z Matomo"

1. Znajdź sekcję "🌐 Import Modeli z Matomo Device Detector"
2. Kliknij przycisk **"🌐 Importuj Modele z Matomo (1000+ modeli)"**
3. Potwierdź w oknie dialogowym
4. Czekaj 10-30 sekund

### Krok 3: Sprawdź Wynik

Po imporcie zobaczysz:

```
✅ Zaimportowano modele z Matomo!
• Nowe modele: 14662
• Zaktualizowane: 0
• Łącznie: 14742
```

Baza zostanie zapisana do pliku `shark_external_db.json` i przetrwa restart aplikacji.

---

## 📊 Co Zawiera Baza?

### Statystyki

- **14,742 modeli** telefonów
- **500+ marek** (Samsung, Apple, Xiaomi, Motorola, OnePlus, Huawei, etc.)
- **Automatyczne mapowanie** ID urządzenia → nazwa modelu

### Przykładowe Modele

```json
{
  "SM-S928": "Samsung Galaxy S24 Ultra",
  "iPhone17,1": "iPhone 16 Pro",
  "XT2301": "Motorola Edge 40",
  "CPH2581": "OnePlus 12",
  "2311DRK48C": "Xiaomi 14 Pro",
  "Pixel 8 Pro": "Google Pixel 8 Pro"
}
```

---

## 🔧 Jak To Działa?

### 1. Skrypt `setup_database.py`

- Pobiera dane z GitHub: `matomo-org/device-detector`
- Parsuje plik YAML: `regexes/device/mobiles.yml`
- Wyciąga ID urządzeń z wyrażeń regularnych
- Mapuje ID → pełna nazwa modelu
- Zapisuje do `shark_external_db.json`

### 2. Aplikacja `shark_v18_cloud.py`

Przy starcie:

```python
def load_data():
    # Załaduj bazę modeli z pliku JSON (jeśli istnieje)
    external_db_file = 'shark_external_db.json'
    if os.path.exists(external_db_file):
        with open(external_db_file, 'r', encoding='utf-8') as f:
            loaded_db = json.load(f)
            EXTERNAL_DB.update(loaded_db)
            logger.info(f"✅ External DB loaded: {len(EXTERNAL_DB)} models")
    else:
        logger.warning(f"⚠️ External DB file not found. Using default models only")
        logger.info("💡 Run 'python setup_database.py' to import 14000+ models")
```

### 3. Rozpoznawanie Urządzeń

System używa 3-poziomowej hierarchii:

1. **User-Agent Exact Match (100%)** - ID z UA → EXTERNAL_DB
2. **AI Brain (85-95%)** - Fingerprint → nauczony model
3. **Heuristics (60-80%)** - Rozdzielczość + GPU + Hz

---

## 📁 Struktura Plików

```
SHARK_v18_RELEASE/
├── shark_v18_cloud.py          # Główna aplikacja
├── setup_database.py           # Skrypt importu (NOWY!)
├── shark_external_db.json      # Baza modeli (generowany)
├── shark_brain_v18.json        # Baza AI (generowany)
├── requirements.txt            # Zależności
└── INSTALACJA_BAZY.md         # Ten plik
```

---

## ⚙️ Wymagania

### Biblioteki Python

```txt
pyyaml==6.0.3
requests==2.32.5
```

Instalacja:

```powershell
pip install pyyaml requests
```

Lub:

```powershell
pip install -r requirements.txt
```

---

## 🐛 Rozwiązywanie Problemów

### Problem 1: "ModuleNotFoundError: No module named 'yaml'"

**Rozwiązanie:**

```powershell
pip install pyyaml
```

### Problem 2: "Brak danych z Matomo"

**Przyczyna:** Brak połączenia z internetem lub GitHub niedostępny

**Rozwiązanie:**

1. Sprawdź połączenie internetowe
2. Spróbuj ponownie za chwilę
3. Sprawdź czy GitHub działa: https://www.githubstatus.com/

### Problem 3: "Timeout podczas importu na Render"

**Przyczyna:** Render Free Tier ma limit 30s na request

**Rozwiązanie:**

1. Uruchom `setup_database.py` **lokalnie**
2. Wypchnij `shark_external_db.json` do repozytorium:

```powershell
git add shark_external_db.json
git commit -m "Add pre-imported database with 14000+ models"
git push origin master
```

3. Render automatycznie wdroży plik z bazą

### Problem 4: "Aplikacja nie widzi modeli"

**Sprawdź:**

```powershell
# Czy plik istnieje?
ls shark_external_db.json

# Ile modeli?
python -c "import json; f=open('shark_external_db.json','r',encoding='utf-8'); data=json.load(f); print(f'Modeli: {len(data)}')"
```

**Rozwiązanie:**

Uruchom ponownie `setup_database.py`

---

## 🚀 Deploy na Render z Bazą

### Opcja A: Import przez Panel Admin (po deploymencie)

1. Deploy aplikacji na Render
2. Wejdź na `/admin`
3. Kliknij "Importuj Modele z Matomo"

### Opcja B: Pre-import (przed deploymentem)

1. **Lokalnie** uruchom `setup_database.py`
2. Wypchnij `shark_external_db.json` do repo:

```powershell
git add shark_external_db.json
git commit -m "Add pre-imported database"
git push origin master
```

3. Render automatycznie wdroży plik
4. Aplikacja od razu ma 14,000+ modeli! ✅

---

## 📊 Weryfikacja

### Test 1: Sprawdź Logi Aplikacji

```
2026-01-30 13:32:40,203 - ✅ External DB loaded: 14742 models
```

### Test 2: Sprawdź Panel Admin

```
https://twoja-domena.onrender.com/admin
```

Statystyki powinny pokazywać:

```
📱 Modeli w Bazie
14742
```

### Test 3: Test Rozpoznawania

Otwórz aplikację na telefonie Motorola:

```
https://twoja-domena.onrender.com/
```

Kliknij "🚀 Rozpocznij Skanowanie"

Powinno rozpoznać:

```
Motorola Edge 40
🧠 PEWNOŚĆ: 100%
```

---

## ✅ Checklist Instalacji

```
□ Zainstalowano pyyaml i requests
□ Uruchomiono setup_database.py
□ Plik shark_external_db.json istnieje
□ Plik zawiera 14000+ modeli
□ Aplikacja wczytuje bazę przy starcie
□ Panel admin pokazuje poprawną liczbę modeli
□ Rozpoznawanie działa dla Motorola/Samsung/iPhone
```

---

## 🎉 Gotowe!

Teraz SHARK v18 ma **14,742 modeli** w bazie i rozpoznaje:

✅ **iPhone** (wszystkie modele od 11 do 17)
✅ **Samsung** (Galaxy S20-S24, A-series, Z Fold/Flip)
✅ **Motorola** (Edge, Moto G, Razr)
✅ **Xiaomi** (14, 13, 12, Mi 11, Redmi)
✅ **OnePlus** (12, 11, 10, 9, 8)
✅ **Google Pixel** (8, 7, 6, 5)
✅ **Huawei** (P40, P30, Mate)
✅ **I 14,000+ innych modeli!**

---

**SHARK v18 - Największa Baza Rozpoznawania Urządzeń Mobilnych!** 🦈📱
