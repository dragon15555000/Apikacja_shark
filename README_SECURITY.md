# SHARK v18 - Ulepszenia Bezpieczeństwa

## 🔒 Zaimplementowane Zabezpieczenia

### 1. **Walidacja JSON**
Wszystkie API endpoints (`/api/check_brain`, `/api/learn`) mają teraz:
- ✅ Sprawdzanie Content-Type (musi być `application/json`)
- ✅ Walidację formatu JSON
- ✅ Sprawdzanie wymaganych pól
- ✅ Walidację typów danych (int, float, string)
- ✅ Walidację zakresów wartości (np. width: 0-10000px)
- ✅ Limity długości stringów (zapobieganie atakom)

### 2. **Rate Limiting**
Zaimplementowano ograniczenia częstotliwości zapytań:
- **Globalne limity**: 200 zapytań/dzień, 50 zapytań/godzinę
- **`/api/check_brain`**: 30 zapytań/minutę
- **`/api/learn`**: 10 zapytań/minutę
- Ochrona przed atakami DDoS i brute-force

### 3. **Error Handling**
- ✅ Proper try-catch bloki we wszystkich funkcjach
- ✅ Szczegółowe logowanie błędów
- ✅ Bezpieczne komunikaty błędów (bez ujawniania szczegółów implementacji)
- ✅ HTTP status codes zgodne ze standardem

### 4. **Dodatkowe Zabezpieczenia**
- ✅ Ochrona przed Regex DoS (limit długości User-Agent do 1000 znaków)
- ✅ Sanityzacja danych wejściowych
- ✅ Docstringi dla lepszej dokumentacji kodu

## 📦 Instalacja

```bash
pip install -r requirements.txt
```

## 🚀 Uruchomienie

```bash
python shark_v18.py
```

## 📊 Przykłady Walidacji

### ✅ Poprawne zapytanie do `/api/check_brain`:
```json
{
  "w": 393,
  "h": 852,
  "hz": 120,
  "gpu": "a17 pro",
  "canvasHash": "abc123def",
  "userAgent": "Mozilla/5.0 (iPhone17,1; ...)"
}
```

### ❌ Niepoprawne zapytania (zwrócą błąd 400):
```json
// Brak wymaganego pola
{"w": 393, "h": 852}

// Nieprawidłowy typ danych
{"w": "abc", "h": 852, "hz": 120, "gpu": "a17", "canvasHash": "xyz"}

// Wartość poza zakresem
{"w": 99999, "h": 852, "hz": 120, "gpu": "a17", "canvasHash": "xyz"}

// Zbyt długi string
{"w": 393, "h": 852, "hz": 120, "gpu": "a17...[300 znaków]", "canvasHash": "xyz"}
```

## 🔍 Monitoring

Wszystkie operacje są teraz logowane:
- Identyfikacje urządzeń (UA_EXACT, UA_RAW, AI)
- Operacje uczenia AI
- Błędy i wyjątki
- Próby naruszenia limitów

## ⚠️ Uwagi

1. **Rate Limiting** używa pamięci in-memory - po restarcie serwera liczniki są resetowane
2. Dla produkcji zaleca się użycie Redis jako storage dla rate limitera:
   ```python
   storage_uri="redis://localhost:6379"
   ```
3. SSL nadal używa `adhoc` - dla produkcji użyj właściwych certyfikatów

## 📝 Changelog

### v18.2 (Performance & Code Quality Update)
- ✅ Dodano thread-safe operacje na BRAIN dictionary (BRAIN_LOCK)
- ✅ Zaimplementowano limit rozmiaru BRAIN (10,000 sygnatur)
- ✅ Dodano limit modeli na sygnaturę (5 modeli)
- ✅ Refaktoryzacja kodu zgodnie z PEP8
- ✅ Poprawiono nazewnictwo zmiennych (descriptive names)
- ✅ Dodano docstringi dla wszystkich funkcji
- ✅ Ulepszone formatowanie i czytelność kodu

### v18.1 (Security Update)
- ✅ Dodano walidację JSON dla wszystkich API endpoints
- ✅ Zaimplementowano rate limiting (Flask-Limiter)
- ✅ Poprawiono error handling i logging
- ✅ Dodano ochronę przed Regex DoS
- ✅ Dodano walidację typów i zakresów danych

## 🔧 Zarządzanie Pamięcią

### Limity BRAIN
- **MAX_BRAIN_SIGNATURES**: 10,000 sygnatur
  - Po osiągnięciu limitu, najstarsza sygnatura jest usuwana (FIFO)
- **MAX_MODELS_PER_SIGNATURE**: 5 modeli na sygnaturę
  - Po osiągnięciu limitu, model z najmniejszą liczbą wystąpień jest usuwany

### Thread Safety
Wszystkie operacje na BRAIN są chronione przez `BRAIN_LOCK`:
- Odczyt sygnatur w `/api/check_brain`
- Zapis nowych danych w `/api/learn`
- Ładowanie i zapisywanie pliku JSON

## 🎯 Najlepsze Praktyki PEP8

### Zaimplementowane:
- ✅ Opisowe nazwy zmiennych (`width`, `height`, `refresh_rate` zamiast `w`, `h`, `hz`)
- ✅ Maksymalna długość linii: 79-100 znaków
- ✅ Docstringi dla wszystkich funkcji
- ✅ Spacje wokół operatorów
- ✅ Konsekwentne wcięcia (4 spacje)
- ✅ Grupowanie importów
- ✅ Komentarze w języku polskim dla czytelności
