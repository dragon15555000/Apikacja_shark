set dotenv-load

# Wyświetl listę dostępnych poleceń
default:
    @just --list

# Konfiguracja środowiska lokalnego i pre-commit
setup:
    if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi
    if [ -f package.json ]; then npm ci; fi
    if command -v pre-commit >/dev/null 2>&1; then pre-commit install; fi

# Walidacja jakości kodu (linter, formatter, testy)
check:
    if command -v ruff >/dev/null 2>&1 && [ -f pyproject.toml -o -d src ]; then ruff check . && ruff format --check .; fi
    if [ -d tests ] && command -v pytest >/dev/null 2>&1; then pytest tests/; fi
    if [ -f package.json ] && grep -q '"test"' package.json; then npm test; fi

# Skanowanie sekretów i prywatnych adresów IP przez Gitleaks
security:
    gitleaks detect --config .gitleaks.toml --redact --verbose

# Zrzut samego schematu lokalnej bazy danych (bez danych)
db-schema-dump:
    @mkdir -p docs/db
    pg_dump --schema-only "${LOCAL_DATABASE_URL:-$DATABASE_URL}" > docs/db/schema.sql

# Uruchomienie usług lokalnych w Dockerze
up:
    docker compose up -d

# Zatrzymanie usług lokalnych (bez usuwania wolumenów)
down:
    docker compose down
