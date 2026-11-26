# Zasady Współpracy (CONTRIBUTING.md)

Dziękujemy za wkład w rozwój projektu! Aby zachować najwyższą jakość i przejrzystość kodu, w repozytorium obowiązują poniższe standardy.

---

## 1. Cykl życia gałęzi (Git Flow)

- `main` – gałąź produkcyjna, chroniona przed bezpośrednimi pushami. Wszystkie zmiany trafiają przez Pull Request.
- `feature/<nazwa>` – nowe funkcjonalności i moduły.
- `fix/<nazwa>` – poprawki błędów.
- `chore/<nazwa>` – zadania porządkowe, konfiguracja, aktualizacje zależności.
- `refactor/<nazwa>` – refaktoryzacja bez zmian funkcjonalnych.

---

## 2. Konwencja Commitów (Conventional Commits)

Format każdego commita:
```
<typ>(<opcjonalny zakres>): <krótki opis w trybie rozkazującym>

[opcjonalna treść szczegółowa]
```

Dozwolone typy:
- `feat:` – nowa funkcja dla użytkownika końcowego
- `fix:` – poprawka błędu
- `refactor:` – zmiana w kodzie nienaprawiająca błędu i niedodająca nowej funkcji
- `test:` – dodanie lub modyfikacja testów
- `docs:` – modyfikacja dokumentacji
- `style:` – formatowanie, brak zmian w logice kodu
- `chore:` – zadania pomocnicze, narzędzia, zależności

---

## 3. Standardy Jakości i Testy

Przed otwarciem Pull Requesta:
1. Upewnij się, że linter i formatter nie zgłaszają błędów (np. `ruff check .` i `ruff format --check .` lub `npm run lint`).
2. Uruchom testy lokalnie i upewnij się, że wszystkie przechodzą (np. `pytest` lub `npm test`).
3. Sprawdź, czy nie dodałeś przypadkowo sekretów (`gitleaks detect`).

---

## 4. Procedura Pull Request

1. Otwórz PR kierowany na gałąź `main`.
2. Wypełnij pola w `.github/PULL_REQUEST_TEMPLATE.md`.
3. Poczekaj na pomyślne przejście pipeline'u CI oraz lokalnego strażnika AI (`ai-gatekeeper`).
