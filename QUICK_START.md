# 🚀 SHARK v18 - Quick Start Guide

## ⚡ Szybki Start (3 kroki)

### 1️⃣ Instalacja (1 minuta)
```powershell
# Przejdź do folderu projektu
cd C:/temo/install_shark/SHARK_v18_Final

# Zainstaluj zależności
pip install -r requirements.txt
```

### 2️⃣ Uruchomienie (10 sekund)
```powershell
# Uruchom aplikację
python shark_v18.py
```

**Zobaczysz:**
```
============================================================
SHARK v18 FINAL | URL: https://192.168.1.100:5000
Brain signatures: 0
Max signatures: 10000
============================================================

█▀▀▀▀▀█ ▀▀█▄▀ █▀▀▀▀▀█
█ ███ █ ▄▀▄█▀ █ ███ █
█ ▀▀▀ █ █▀▀▄█ █ ▀▀▀ █
▀▀▀▀▀▀▀ ▀ ▀ ▀ ▀▀▀▀▀▀▀
```

### 3️⃣ Użycie (1 kliknięcie)
```
1. Otwórz URL na iPhone/iPad
2. Kliknij "🚀 Rozpocznij Skanowanie"
3. Gotowe! ✅
```

---

## 📱 Jak Używać

### Scenariusz 1: Identyfikacja Urządzenia
```
iPhone → Otwórz URL → Skanuj → Zobacz wynik
```

**Przykładowy wynik:**
```
┌─────────────────────────────┐
│   iPhone 16 Pro             │
│   🧠 PEWNOŚĆ: 100%          │
└─────────────────────────────┘

Parametry:
• Rozdzielczość: 402 × 874
• Odświeżanie: 120 Hz
• GPU: A18 Pro
```

### Scenariusz 2: Nauczenie AI
```
Skanuj → Jeśli błędny wynik → Wybierz poprawny → Zapisz
```

**System zapamięta:**
- Następnym razem rozpozna automatycznie
- Pewność rośnie z każdym skanowaniem
- Działa nawet bez User-Agent

---

## 🔧 Konfiguracja

### Zmiana Portu
```python
# W shark_v18.py, linia ~395
app.run(
    host='0.0.0.0',
    port=8080,  # ← Zmień tutaj
    ssl_context='adhoc',
    debug=False,
    threaded=True
)
```

### Zmiana Limitów
```python
# W shark_v18.py, linia ~19
MAX_BRAIN_SIGNATURES = 20000  # ← Zwiększ limit
MAX_MODELS_PER_SIGNATURE = 10  # ← Więcej modeli
```

### Zmiana Rate Limiting
```python
# W shark_v18.py, linia ~95
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"],  # ← Zmień
    storage_uri="memory://"
)
```

---

## 🐛 Rozwiązywanie Problemów

### Problem: Port 5000 zajęty
```powershell
# Sprawdź co używa portu
netstat -ano | findstr :5000

# Zabij proces (zamień PID)
taskkill /PID 12345 /F

# LUB zmień port w kodzie
```

### Problem: Brak połączenia z iPhone
```powershell
# Sprawdź IP
ipconfig

# Sprawdź firewall
New-NetFirewallRule -DisplayName "SHARK" -Direction Inbound -Port 5000 -Protocol TCP -Action Allow

# Sprawdź czy oba urządzenia w tej samej sieci WiFi
```

### Problem: SSL Certificate Error
```
Na iPhone:
1. Otwórz URL mimo ostrzeżenia
2. Settings → General → About
3. Certificate Trust Settings
4. Włącz dla localhost
```

### Problem: ModuleNotFoundError
```powershell
# Zainstaluj ponownie wszystkie zależności
pip install -r requirements.txt --force-reinstall

# Sprawdź instalację
pip list | Select-String -Pattern "flask"
```

### Problem: QR Code nie wyświetla się
```powershell
# Zainstaluj qrcode
pip install qrcode --upgrade

# Jeśli nadal nie działa, zignoruj - użyj URL bezpośrednio
```

---

## 📊 Przydatne Komendy

### Sprawdź Status
```powershell
# Ile sygnatur w BRAIN
Get-Content shark_brain_v18.json | ConvertFrom-Json |
    Select-Object -ExpandProperty PSObject.Properties |
    Measure-Object | Select-Object Count

# Ostatnie logi
Get-Content shark_logs_v18.csv -Tail 10
```

### Wyczyść Dane
```powershell
# Usuń BRAIN (zaczynamy od zera)
Remove-Item shark_brain_v18.json

# Usuń logi
Remove-Item shark_logs_v18.csv
```

### Backup Danych
```powershell
# Backup BRAIN
Copy-Item shark_brain_v18.json shark_brain_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').json

# Restore
Copy-Item shark_brain_backup_20250115_143022.json shark_brain_v18.json
```

---

## 🎯 Najlepsze Praktyki

### Dla Użytkowników
1. ✅ Zawsze skanuj w dobrym oświetleniu
2. ✅ Upewnij się że WiFi jest stabilne
3. ✅ Jeśli wynik niepewny - naucz AI
4. ✅ Skanuj ponownie dla weryfikacji

### Dla Administratorów
1. ✅ Regularnie rób backup BRAIN
2. ✅ Monitoruj logi pod kątem błędów
3. ✅ Sprawdzaj rozmiar BRAIN (max 10,000)
4. ✅ Aktualizuj zależności co miesiąc

### Dla Developerów
1. ✅ Czytaj logi w czasie rzeczywistym
2. ✅ Testuj z różnymi urządzeniami
3. ✅ Dokumentuj nowe modele
4. ✅ Commituj zmiany regularnie

---

## 📈 Metryki Wydajności

### Oczekiwane Wartości
```
Response Time:        < 100ms
Memory Usage:         < 50MB
CPU Usage:            < 5%
Concurrent Users:     50+
Uptime:               99.9%
```

### Jak Mierzyć
```powershell
# Response time
Measure-Command {
    Invoke-RestMethod -Uri "https://localhost:5000/api/check_brain" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"w":393,"h":852,"hz":60,"gpu":"a16","canvasHash":"test"}' `
        -SkipCertificateCheck
}

# Memory usage
Get-Process python | Select-Object WorkingSet
```

---

## 🔐 Bezpieczeństwo - Checklist

### Przed Wdrożeniem Produkcyjnym
- [ ] Zmień adhoc SSL na właściwy certyfikat
- [ ] Skonfiguruj reverse proxy (nginx)
- [ ] Włącz HTTPS redirect
- [ ] Ustaw silniejsze rate limiting
- [ ] Dodaj authentication (jeśli potrzebne)
- [ ] Skonfiguruj monitoring
- [ ] Ustaw automatyczne backupy
- [ ] Przetestuj pod obciążeniem

### Regularne Sprawdzanie
- [ ] Aktualizuj zależności (pip list --outdated)
- [ ] Sprawdzaj logi pod kątem ataków
- [ ] Monitoruj rozmiar BRAIN
- [ ] Weryfikuj certyfikat SSL
- [ ] Testuj rate limiting

---

## 📚 Dokumentacja

### Pliki Projektu
```
SHARK_v18_Final/
├── shark_v18.py           # Główna aplikacja
├── requirements.txt       # Zależności
├── README_SECURITY.md     # Bezpieczeństwo
├── CHANGELOG.md           # Historia zmian
├── PREZENTACJA.md         # Prezentacja projektu
├── DEMO_SCRIPT.md         # Skrypt demo
├── QUICK_START.md         # Ten plik
├── shark_brain_v18.json   # Baza AI (generowana)
└── shark_logs_v18.csv     # Logi (generowane)
```

### Przydatne Linki
- **Flask Docs**: https://flask.palletsprojects.com/
- **Flask-Limiter**: https://flask-limiter.readthedocs.io/
- **PEP8 Style Guide**: https://pep8.org/

---

## 🎓 Nauka Więcej

### Jak Działa Fingerprinting?
```javascript
// Rozdzielczość
const width = Math.min(screen.width, screen.height);
const height = Math.max(screen.width, screen.height);

// Częstotliwość odświeżania
function measureHz() {
    let frames = 0;
    const start = performance.now();
    function loop() {
        frames++;
        if (performance.now() - start >= 500) {
            return Math.round(frames * 2) < 70 ? 60 : 120;
        }
        requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);
}

// GPU
const canvas = document.createElement('canvas');
const gl = canvas.getContext('webgl');
const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
const gpu = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
```

### Jak Działa AI Learning?
```python
# Sygnatura = unikalna kombinacja parametrów
signature = f"{width}_{height}_{hz}_{gpu}_{canvas_hash}"

# BRAIN = dict of dicts
BRAIN = {
    "402_874_120_a18_abc123": {
        "iPhone 16 Pro": 15,  # 15 skanowań
        "iPhone 15 Pro": 2    # 2 skanowania
    }
}

# Wybór modelu = model z największą liczbą wystąpień
top_model = max(models, key=models.get)  # iPhone 16 Pro
confidence = (15 / 17) * 100  # 88%
```

---

## 💡 Tips & Tricks

### Szybkie Testowanie
```powershell
# Test endpoint bez iPhone
$body = @{
    w = 393
    h = 852
    hz = 60
    gpu = "a16"
    canvasHash = "test123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://localhost:5000/api/check_brain" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body `
    -SkipCertificateCheck
```

### Debug Mode
```python
# W shark_v18.py, zmień:
app.run(
    host='0.0.0.0',
    port=5000,
    ssl_context='adhoc',
    debug=True,  # ← Włącz debug
    threaded=True
)
```

### Verbose Logging
```python
# W shark_v18.py, zmień:
logging.basicConfig(
    level=logging.DEBUG,  # ← Zmień z INFO na DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

---

## 🎉 Gotowe!

Teraz możesz:
- ✅ Uruchomić SHARK v18
- ✅ Identyfikować urządzenia
- ✅ Uczyć AI
- ✅ Rozwiązywać problemy
- ✅ Konfigurować system

**Potrzebujesz pomocy?**
- 📖 Czytaj: `README_SECURITY.md`
- 🎬 Demo: `DEMO_SCRIPT.md`
- 📊 Prezentacja: `PREZENTACJA.md`
- 📝 Historia: `CHANGELOG.md`

---

**Miłego korzystania z SHARK v18!** 🦈✨
