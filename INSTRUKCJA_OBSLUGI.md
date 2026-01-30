# 📱 SHARK v18 - Instrukcja Obsługi

## 🚀 Szybki Start

### 1. Uruchomienie Systemu

```bash
python shark_v18.py
```

Po uruchomieniu zobaczysz:
```
============================================================
SHARK v18 FINAL | URL: https://192.168.1.100:5000
Brain signatures: 0
Max signatures: 10000
============================================================

[QR CODE]
```

### 2. Dostęp z Telefonu

**Opcja A: Zeskanuj QR Code**
- Otwórz aparat w telefonie
- Zeskanuj kod QR z konsoli
- Kliknij link

**Opcja B: Wpisz adres ręcznie**
- Otwórz przeglądarkę w telefonie
- Wpisz adres z konsoli (np. `https://192.168.1.100:5000`)
- Zaakceptuj certyfikat (kliknij "Zaawansowane" → "Przejdź")

### 3. Skanowanie Telefonu

1. Kliknij **"🚀 Rozpocznij Skanowanie"**
2. Poczekaj 2-3 sekundy
3. System wyświetli:
   - **Model telefonu** (np. "Samsung Galaxy S24 Ultra")
   - **Pewność rozpoznania** (np. "🧠 PEWNOŚĆ: 100%")
   - **Kod szybki** (np. "SA1U1")
   - **Kody akcesoriów** (szkło i etui)

## 📊 Interfejs Użytkownika

### Ekran Główny

```
┌─────────────────────────────────┐
│ SHARK v18    ONLINE • HTTPS     │
├─────────────────────────────────┤
│                                 │
│   Samsung Galaxy S24 Ultra      │
│   🧠 PEWNOŚĆ: 100%              │
│                                 │
├─────────────────────────────────┤
│  🚀 Rozpocznij Skanowanie       │
├─────────────────────────────────┤
│                                 │
│   📱 Kod Szybki                 │
│        SA1U1                    │
│   Podaj ten kod sprzedawcy      │
│                                 │
├─────────────────────────────────┤
│ Dostępne Akcesoria              │
├─────────────────────────────────┤
│ 🛡️ Szkło Ochronne    SA1U1     │
│ 📦 Etui              SA1U2      │
├─────────────────────────────────┤
│ Parametry                       │
├─────────────────────────────────┤
│ Rozdzielczość      412 x 915    │
│ Odświeżanie        120 Hz       │
│ GPU                Adreno 740   │
│ Canvas Hash        a3f2b1c      │
│ UA System          Mozilla/5... │
├─────────────────────────────────┤
│ Korekta AI                      │
├─────────────────────────────────┤
│ [Wybierz model ▼]               │
│ Zapisz i Naucz AI               │
└─────────────────────────────────┘
```

## 🎯 Scenariusze Użycia

### Scenariusz 1: Klient z iPhone

**Klient**: "Potrzebuję szkło na iPhone 16 Pro"

**Ty**:
1. Podaj klientowi link/QR code
2. Klient skanuje telefon
3. System pokazuje: **iPhone 16 Pro** + kod **B2U1**
4. Podajesz szkło z kodem **B2U1**

✅ **Czas: 10 sekund**

### Scenariusz 2: Klient z Samsung

**Klient**: "Mam Samsunga, nie wiem jaki model"

**Ty**:
1. Klient skanuje telefon
2. System pokazuje: **Samsung Galaxy S23 Ultra** + kod **SB1U1**
3. Podajesz szkło **SB1U1** i etui **SB1U2**

✅ **Czas: 10 sekund**

### Scenariusz 3: Nieznany Model

**System pokazuje**: "Nieznany" lub błędny model

**Ty**:
1. Przewiń w dół do "Korekta AI"
2. Wybierz poprawny model z listy
3. Kliknij **"Zapisz i Naucz AI"**
4. System zapamięta ten telefon

✅ **Następnym razem rozpozna automatycznie!**

## 🧠 Uczenie AI

### Kiedy uczyć system?

- ❌ Model rozpoznany błędnie
- ❌ System pokazuje "Nieznany"
- ❌ Pewność poniżej 80%

### Jak nauczyć?

1. **Przewiń do sekcji "Korekta AI"**
2. **Wybierz poprawny model** z listy rozwijanej
3. **Kliknij "Zapisz i Naucz AI"**
4. **Gotowe!** System pokazuje: "✅ Nauczono!"

### Co się dzieje?

System zapisuje unikalny "odcisk palca" telefonu:
- Rozdzielczość ekranu
- Częstotliwość odświeżania
- Typ GPU
- Canvas fingerprint
- User-Agent

Następnym razem ten sam telefon zostanie rozpoznany z **95-100% pewnością**!

## 📋 Kody Akcesoriów - Przewodnik

### iPhone

| Model | Szkło | Etui |
|-------|-------|------|
| iPhone 17 Pro Max | A1U1 | A1U2 |
| iPhone 17 Pro | A2U1 | A2U2 |
| iPhone 16 Pro Max | B1U1 | B1U2 |
| iPhone 16 Pro | B2U1 | B2U2 |
| iPhone 16 | B3U1 | B3U2 |
| iPhone 15 Pro Max | C1U1 | C1U2 |
| iPhone 15 Pro | C2U1 | C2U2 |
| iPhone 15 | C3U1 | C3U2 |
| iPhone 14 Pro Max | D1U1 | D1U2 |
| iPhone 14 Pro | D2U1 | D2U2 |
| iPhone 14 | D3U1 | D3U2 |
| iPhone 13 Pro Max | E1U1 | E1U2 |
| iPhone 13 | E3U1 | E3U2 |
| iPhone 12 | F3U1 | F3U2 |
| iPhone 11 | G3U1 | G3U2 |

### Samsung Galaxy S

| Model | Szkło | Etui |
|-------|-------|------|
| S24 Ultra | SA1U1 | SA1U2 |
| S24+ | SA2U1 | SA2U2 |
| S24 | SA3U1 | SA3U2 |
| S23 Ultra | SB1U1 | SB1U2 |
| S23+ | SB2U1 | SB2U2 |
| S23 | SB3U1 | SB3U2 |
| S22 Ultra | SC1U1 | SC1U2 |
| S22+ | SC2U1 | SC2U2 |
| S22 | SC3U1 | SC3U2 |
| S21 Ultra | SD1U1 | SD1U2 |
| S21+ | SD2U1 | SD2U2 |
| S21 | SD3U1 | SD3U2 |

### Samsung Galaxy A

| Model | Szkło | Etui |
|-------|-------|------|
| A54 | AA1U1 | AA1U2 |
| A53 | AA2U1 | AA2U2 |
| A52 | AA3U1 | AA3U2 |
| A34 | AA4U1 | AA4U2 |
| A33 | AA5U1 | AA5U2 |

### Samsung Galaxy Z (Składane)

| Model | Szkło | Etui |
|-------|-------|------|
| Z Fold 5 | ZF1U1 | ZF1U2 |
| Z Fold 4 | ZF2U1 | ZF2U2 |
| Z Fold 3 | ZF3U1 | ZF3U2 |
| Z Flip 5 | ZP1U1 | ZP1U2 |
| Z Flip 4 | ZP2U1 | ZP2U2 |
| Z Flip 3 | ZP3U1 | ZP3U2 |

### Google Pixel

| Model | Szkło | Etui |
|-------|-------|------|
| Pixel 8 Pro | GP1U1 | GP1U2 |
| Pixel 8 | GP2U1 | GP2U2 |
| Pixel 7 Pro | GP3U1 | GP3U2 |
| Pixel 7 | GP4U1 | GP4U2 |
| Pixel 6 Pro | GP5U1 | GP5U2 |
| Pixel 6 | GP6U1 | GP6U2 |

### Xiaomi

| Model | Szkło | Etui |
|-------|-------|------|
| 14 Pro | XM1U1 | XM1U2 |
| 14 | XM2U1 | XM2U2 |
| 13 Ultra | XM3U1 | XM3U2 |
| 13 Pro | XM4U1 | XM4U2 |
| 13 | XM5U1 | XM5U2 |
| 12 Pro | XM6U1 | XM6U2 |
| 12 | XM7U1 | XM7U2 |

### OnePlus

| Model | Szkło | Etui |
|-------|-------|------|
| 12 | OP1U1 | OP1U2 |
| 11 | OP2U1 | OP2U2 |
| 10 Pro | OP3U1 | OP3U2 |
| 9 Pro | OP4U1 | OP4U2 |
| 9 | OP5U1 | OP5U2 |
| 8 Pro | OP6U1 | OP6U2 |

## 🔍 Rozwiązywanie Problemów

### Problem: "Nieznany" model

**Przyczyna**: Telefon nie jest w bazie lub fingerprint jest unikalny

**Rozwiązanie**:
1. Sprawdź parametry (rozdzielczość, GPU)
2. Użyj "Korekta AI" i wybierz model
3. Kliknij "Zapisz i Naucz AI"

### Problem: Błędny model

**Przyczyna**: Podobne parametry (np. S23 vs S23+)

**Rozwiązanie**:
1. Sprawdź fizycznie model (Ustawienia → O telefonie)
2. Użyj "Korekta AI"
3. Naucz system

### Problem: Niska pewność (< 80%)

**Przyczyna**: Konflikt w bazie AI (wiele modeli z tym samym fingerprintem)

**Rozwiązanie**:
1. Zweryfikuj model fizycznie
2. Naucz ponownie system
3. Im więcej nauczysz, tym wyższa pewność

### Problem: Certyfikat SSL

**Komunikat**: "Połączenie nie jest bezpieczne"

**Rozwiązanie**:
1. Kliknij "Zaawansowane"
2. Kliknij "Przejdź do ... (niebezpieczne)"
3. To normalne dla lokalnego serwera

### Problem: Nie można połączyć

**Przyczyna**: Telefon i komputer w różnych sieciach

**Rozwiązanie**:
1. Upewnij się, że oba urządzenia są w tej samej sieci WiFi
2. Sprawdź firewall (może blokować port 5000)
3. Sprawdź adres IP w konsoli

## 💡 Wskazówki Pro

### 1. Szybkie Skanowanie
- Przygotuj QR code na wydruku
- Klient skanuje sam
- Ty widzisz wynik na swoim ekranie (opcjonalnie)

### 2. Batch Learning
- Na koniec dnia przejrzyj logi
- Naucz system wszystkich nieznanych modeli
- Następnego dnia system będzie mądrzejszy

### 3. Backup Brain
```bash
# Kopia zapasowa
copy shark_brain_v18.json shark_brain_backup.json

# Przywracanie
copy shark_brain_backup.json shark_brain_v18.json
```

### 4. Czyszczenie Brain
Jeśli baza jest zbyt duża lub zawiera błędy:
```bash
# Usuń plik
del shark_brain_v18.json

# Uruchom ponownie - system utworzy nową bazę
python shark_v18.py
```

### 5. Monitoring
Sprawdzaj logi w konsoli:
```
Device identified via UA_EXACT: Samsung Galaxy S24 Ultra
AI learned: iPhone 16 Pro
Device not found in brain
```

## 📊 Statystyki Rozpoznawania

### Metody rozpoznawania:

1. **UA_EXACT** (User-Agent)
   - Dokładność: **100%**
   - Źródło: Kod modelu w User-Agent
   - Przykład: `SM-S928B` → S24 Ultra

2. **AI** (Brain)
   - Dokładność: **85-95%**
   - Źródło: Nauczony fingerprint
   - Wymaga: Wcześniejsze nauczenie

3. **ALGORYTM** (Heuristics)
   - Dokładność: **60-80%**
   - Źródło: Dopasowanie parametrów
   - Fallback gdy UA i AI zawiodą

## 🎓 Szkolenie Pracowników

### Dzień 1: Podstawy
- Uruchomienie systemu
- Skanowanie telefonu
- Odczytywanie kodów

### Dzień 2: AI
- Uczenie systemu
- Korekta błędów
- Weryfikacja modeli

### Dzień 3: Zaawansowane
- Troubleshooting
- Backup/restore
- Monitoring

## 📞 Wsparcie

### Częste Pytania

**Q: Czy system działa offline?**
A: Tak, po uruchomieniu działa w sieci lokalnej bez internetu.

**Q: Ile urządzeń może skanować jednocześnie?**
A: System obsługuje wielu użytkowników jednocześnie (thread-safe).

**Q: Czy dane są wysyłane do internetu?**
A: NIE. Wszystko działa lokalnie.

**Q: Jak często aktualizować bazę modeli?**
A: Przy nowych modelach telefonów (raz na kilka miesięcy).

**Q: Czy mogę zmienić kody akcesoriów?**
A: Tak, edytuj `ACCESSORY_CODES` w pliku `shark_v18.py`.

---

## ✅ Checklist Dzienna

**Rano:**
- [ ] Uruchom `python shark_v18.py`
- [ ] Sprawdź czy QR code się wyświetla
- [ ] Przetestuj skanowanie na swoim telefonie

**W ciągu dnia:**
- [ ] Ucz system przy nieznanych modelach
- [ ] Sprawdzaj pewność rozpoznawania
- [ ] Notuj problematyczne modele

**Wieczorem:**
- [ ] Przejrzyj logi
- [ ] Zrób backup brain (opcjonalnie)
- [ ] Zamknij system (Ctrl+C)

---

**SHARK v18** - Prosta obsługa, potężne możliwości! 🦈
