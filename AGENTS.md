# Wytyczne dla Agentów AI (AGENTS.md)

Repozytorium podlega automatycznemu audytowi jakości i bezpieczeństwa. Każdy agent AI (oraz deweloper) ma obowiązek przestrzegać poniższych ram:

## 1. Zasady Ogólne
- Komentarze, dokumentacja i commity tworzone zgodnie ze standardami projektu.
- NIGDY nie usuwaj, nie komentuj ani nie wyłączaj istniejących testów, chyba że polecenie wprost tego wymaga.
- Każda zmiana logiki biznesowej musi posiadać odpowiednie testy w katalogu `tests/`.

## 2. Ramy Architektoniczne i Higiena Kodu
- Separacja warstw: logika domenowa i biznesowa powinna być odseparowana od wejścia/wyjścia (API, baza danych, UI).
- Unikaj twardych zależności tam, gdzie zalecany jest interfejs / adapter.
- Do testów z bazami danych lub usługami zewnętrznymi używaj kontenerów Docker / Testcontainers lub lokalnych instancji testowych.

## 3. Bezpieczeństwo i Sekrety
- BEZWZGLĘDNY ZAKAZ commitowania jakichkolwiek kluczy API, tokenów, haseł produkcyjnych lub plików `.env`.
- Wszystkie konfiguracje wrażliwe muszą być odczytywane ze zmiennych środowiskowych udokumentowanych w `.env.example`.
- Przed zatwierdzeniem zmian upewnij się, że `gitleaks` nie zgłasza żadnych znalezisk.

## 4. Procedura PR i Weryfikacja
- Każdy Pull Request musi wypełniać szablon `.github/PULL_REQUEST_TEMPLATE.md`.
- PR jest weryfikowany przez lokalnego strażnika AI (`.github/workflows/ai-gatekeeper.yml`) na self-hosted runnerze.
