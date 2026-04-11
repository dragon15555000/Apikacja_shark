# 🚀 SHARK v18 - Przewodnik Instalacji

## 📋 Wymagania Systemowe

### System Operacyjny
- ✅ Windows 10/11
- ✅ macOS 10.15+
- ✅ Linux (Ubuntu 20.04+, Debian, Fedora)

### Oprogramowanie
- **Python 3.8 lub nowszy** (zalecane: Python 3.10+)
- **pip** (menedżer pakietów Python)
- **Dostęp do sieci lokalnej** (WiFi)

### Sprzęt
- **RAM**: Minimum 2 GB (zalecane: 4 GB+)
- **Dysk**: 100 MB wolnego miejsca
- **Sieć**: WiFi lub Ethernet

---

## 📥 Instalacja Krok po Kroku

### Krok 1: Sprawdź Wersję Python

#### Windows:
```powershell
python --version
```

#### macOS/Linux:
```bash
python3 --version
```

**Oczekiwany wynik:**
```
Python 3.10.x
```

> ⚠️ Jeśli Python nie jest zainstalowany, pobierz go z [python.org](https://www.python.org/downloads/)

---

### Krok 2: Pobierz SHARK v18

#### Opcja A: Rozpakuj archiwum
```powershell
# Rozpakuj SHARK_v18_RELEASE.zip do wybranego folderu
# Np. C:\shark\ lub ~/shark/
```

#### Opcja B: Sklonuj repozytorium (jeśli dostępne)
```bash
git clone https://github.com/your-repo/shark-v18.git
cd shark-v18
```

---

### Krok 3: Zainstaluj Zależności

#### Windows:
```powershell
cd C:\temo\install_shark\SHARK_v18_RELEASE
pip install -r requirements.txt
```

#### macOS/Linux:
```bash
cd ~/shark/SHARK_v18_RELEASE
pip3 install -r requirements.txt
```

**Instalowane pakiety:**
- `flask` - Web framework
- `flask-cors` - Cross-Origin Resource Sharing
- `flask-limiter` - Rate limiting
- `qrcode` - Generowanie kodów QR
- `pillow` - Obsługa obrazów

**Czas instalacji:** ~1-2 minuty

---

### Krok 4: Uruchom SHARK

#### Windows:
```powershell
python shark_v18.py
```

#### macOS/Linux:
```bash
python3 shark_v18.py
```

**Oczekiwany wynik:**
```
============================================================
SHARK v18 FINAL | URL: https://192.168.1.100:5000
Brain signatures: 0
Max signatures: 10000
============================================================

█▀▀▀▀▀█ ▀▀█▄▀ █▀▀▀▀▀█
█ ███ █ ▄▀▀█▄ █ ███ █
█ ▀▀▀ █ █▀▄▀█ █ ▀▀▀ █
▀▀▀▀▀▀▀ ▀ ▀ ▀ ▀▀▀▀▀▀▀

 * Serving Flask app 'shark_v18'
 * Running on https://0.0.0.0:5000
```

✅ **System działa!**

---

## 🔧 Rozwiązywanie Problemów Instalacji

### Problem 1: "python nie jest rozpoznawany"

**Windows:**
```powershell
# Dodaj Python do PATH lub użyj pełnej ścieżki:
C:\Python310\python.exe shark_v18.py
```

**macOS/Linux:**
```bash
# Użyj python3 zamiast python:
python3 shark_v18.py
```

---

### Problem 2: "pip nie jest rozpoznawany"

**Windows:**
```powershell
python -m pip install -r requirements.txt
```

**macOS/Linux:**
```bash
python3 -m pip install -r requirements.txt
```

---

### Problem 3: Błąd instalacji pakietów

**Rozwiązanie 1: Aktualizuj pip**
```bash
python -m pip install --upgrade pip
```

**Rozwiązanie 2: Użyj środowiska wirtualnego**
```bash
# Utwórz venv
python -m venv venv

# Aktywuj (Windows)
venv\Scripts\activate

# Aktywuj (macOS/Linux)
source venv/bin/activate

# Zainstaluj pakiety
pip install -r requirements.txt
```

---

### Problem 4: Port 5000 zajęty

**Błąd:**
```
OSError: [Errno 48] Address already in use
```

**Rozwiązanie:**

Edytuj `shark_v18.py` (linia ~498):
```python
app.run(
    host='0.0.0.0',
    port=5001,  # Zmień na 5001 lub inny wolny port
    ssl_context='adhoc',
    debug=False,
    threaded=True
)
```

---

### Problem 5: Firewall blokuje połączenie

**Windows:**
```powershell
# Dodaj regułę firewall:
netsh advfirewall firewall add rule name="SHARK v18" dir=in action=allow protocol=TCP localport=5000
```

**macOS:**
```bash
# System Preferences → Security & Privacy → Firewall → Firewall Options
# Dodaj Python do dozwolonych aplikacji
```

**Linux (UFW):**
```bash
sudo ufw allow 5000/tcp
```

---

### Problem 6: Brak modułu SSL

**Błąd:**
```
ImportError: No module named '_ssl'
```

**Windows:**
```powershell
# Zainstaluj OpenSSL
# Pobierz z: https://slproweb.com/products/Win32OpenSSL.html
```

**Ubuntu/Debian:**
```bash
sudo apt-get install libssl-dev
```

**macOS:**
```bash
brew install openssl
```

---

## 🌐 Konfiguracja Sieci

### Sprawdź Adres IP

#### Windows:
```powershell
ipconfig
```
Szukaj: `IPv4 Address`

#### macOS/Linux:
```bash
ifconfig
# lub
ip addr show
```
Szukaj: `inet 192.168.x.x`

### Połącz Telefon z Tą Samą Siecią WiFi

1. Otwórz ustawienia WiFi w telefonie
2. Połącz się z tą samą siecią co komputer
3. Zeskanuj QR code lub wpisz adres ręcznie

---

## 📱 Pierwsze Uruchomienie

### 1. Otwórz Przeglądarkę na Telefonie

Wpisz adres z konsoli:
```
https://192.168.1.100:5000
```

### 2. Zaakceptuj Certyfikat SSL

**Komunikat:** "Połączenie nie jest bezpieczne"

**Kliknij:**
- Chrome/Safari: "Zaawansowane" → "Przejdź do ... (niebezpieczne)"
- Firefox: "Zaawansowane" → "Akceptuj ryzyko i kontynuuj"

> ℹ️ To normalne dla lokalnego serwera z self-signed certificate

### 3. Przetestuj Skanowanie

1. Kliknij **"🚀 Rozpocznij Skanowanie"**
2. Poczekaj 2-3 sekundy
3. Sprawdź czy model został rozpoznany

✅ **Jeśli widzisz model telefonu - instalacja zakończona sukcesem!**

---

## 🔄 Aktualizacja

### Z v17 do v18

1. **Backup brain:**
```powershell
copy shark_brain_v17.json shark_brain_backup.json
```

2. **Zastąp pliki:**
```powershell
# Skopiuj nowy shark_v18.py
```

3. **Uruchom:**
```powershell
python shark_v18.py
```

> ℹ️ Brain z v17 jest kompatybilny z v18

---

## 🗑️ Deinstalacja

### Usuń Pakiety Python
```bash
pip uninstall flask flask-cors flask-limiter qrcode pillow -y
```

### Usuń Pliki
```powershell
# Windows
rmdir /s /q C:\temo\install_shark\SHARK_v18_RELEASE

# macOS/Linux
rm -rf ~/shark/SHARK_v18_RELEASE
```

### Usuń Środowisko Wirtualne (jeśli używane)
```bash
deactivate
rm -rf venv
```

---

## 📊 Weryfikacja Instalacji

### Checklist

- [ ] Python 3.8+ zainstalowany
- [ ] Wszystkie pakiety z requirements.txt zainstalowane
- [ ] shark_v18.py uruchamia się bez błędów
- [ ] QR code wyświetla się w konsoli
- [ ] Przeglądarka otwiera się automatycznie
- [ ] Telefon może połączyć się z serwerem
- [ ] Skanowanie działa poprawnie

### Test Funkcjonalności

```bash
# 1. Uruchom serwer
python shark_v18.py

# 2. Otwórz w przeglądarce (na komputerze)
https://localhost:5000

# 3. Kliknij "Rozpocznij Skanowanie"

# 4. Sprawdź logi w konsoli:
# - "Device identified via..."
# - Brak błędów
```

---

## 🆘 Wsparcie

### Logi

Sprawdź logi w konsoli:
```
2025-01-15 10:30:45 - Brain loaded: 0 signatures
2025-01-15 10:30:46 - Device identified via UA_EXACT: ...
```

### Pliki Diagnostyczne

- `shark_logs_v18.csv` - Historia skanowań
- `shark_brain_v18.json` - Baza AI
- Logi konsoli - Błędy runtime

### Zgłaszanie Problemów

Przy zgłaszaniu problemu podaj:
1. System operacyjny i wersja
2. Wersja Python (`python --version`)
3. Pełny komunikat błędu
4. Logi z konsoli
5. Kroki do reprodukcji

---

## 🎓 Następne Kroki

Po instalacji:

1. 📖 Przeczytaj [INSTRUKCJA_OBSLUGI.md](INSTRUKCJA_OBSLUGI.md)
2. 📋 Zapoznaj się z [KODY_AKCESORIOW.txt](KODY_AKCESORIOW.txt)
3. 📝 Sprawdź [README.md](README.md) dla szczegółów technicznych
4. 🔄 Zobacz [CHANGELOG.md](CHANGELOG.md) dla historii zmian

---

## ✅ Instalacja Zakończona!

**SHARK v18 jest gotowy do użycia!** 🦈

Uruchom system:
```bash
python shark_v18.py
```

I zacznij skanować telefony! 📱

---

**Wersja dokumentu:** 1.0
**Data:** 2025-01-15
**System:** SHARK v18
