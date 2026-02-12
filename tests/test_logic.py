"""
SHARK v18 - Testy Jednostkowe dla Logiki Biznesowej

Ten plik zawiera testy dla funkcji w `app/logic.py`.
Używamy `pytest` i `pytest-mock` do testowania w izolacji.

Aby uruchomić testy:
    pytest tests/
"""
import sys
import os

# Dodaj główny katalog projektu do ścieżki, aby umożliwić import modułów aplikacji
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app.logic import parse_device_from_ua, find_top_3_matches


# --- Testy dla funkcji parse_device_from_ua ---

def test_parse_device_from_ua_iphone():
    """Testuje, czy poprawnie parsuje identyfikator iPhone."""
    ua_string = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1 (model:iPhone16,1)"
    expected_id = "iPhone16,1"
    assert parse_device_from_ua(ua_string) == expected_id

def test_parse_device_from_ua_samsung():
    """Testuje, czy poprawnie parsuje identyfikator Samsung."""
    ua_string = "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
    expected_id = "SM-S928"
    assert parse_device_from_ua(ua_string) == expected_id

def test_parse_device_from_ua_unknown():
    """Testuje, czy zwraca None dla nieznanego User-Agent."""
    ua_string = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    assert parse_device_from_ua(ua_string) is None


# --- Testy dla funkcji find_top_3_matches ---

def test_find_top_3_perfect_match_iphone(mocker):
    """
    Testuje idealne dopasowanie dla iPhone 15 Pro Max.
    Mockujemy (zaślepiamy) połączenie z bazą danych, aby test był jednostkowy.
    """
    # Zaślep połączenie z bazą danych, aby funkcja korzystała tylko z HEURISTIC_DB
    mocker.patch('app.logic.db', None)

    # Dane wejściowe idealnie pasujące do iPhone 15 Pro Max
    params = {
        "width": 430, "height": 932, "refresh_rate": 120,
        "gpu": "apple a17 pro gpu", "dpr": 3.0, "ram": -1, "cores": 8
    }

    matches = find_top_3_matches(**params)

    # Sprawdzamy, czy otrzymaliśmy jakieś wyniki
    assert len(matches) > 0
    # Sprawdzamy, czy najlepszy wynik to iPhone 15 Pro Max
    assert matches[0]['model'] == "iPhone 15 Pro Max"
    # Sprawdzamy, czy pewność jest wysoka (powinna być 100)
    assert matches[0]['confidence'] >= 95

def test_find_top_3_android_match(mocker):
    """Testuje dopasowanie dla urządzenia z Androidem (Samsung S24 Ultra)."""
    mocker.patch('app.logic.db', None)

    # Dane wejściowe dla Samsung Galaxy S24 Ultra
    params = {
        "width": 384, "height": 824, "refresh_rate": 120,
        "gpu": "adreno (tm) 750", "dpr": 3.75, "ram": 8, "cores": 8
    }

    matches = find_top_3_matches(**params)

    assert len(matches) > 0
    assert matches[0]['model'] == "Samsung Galaxy S24 Ultra"
    assert matches[0]['confidence'] >= 90

def test_find_top_3_no_match(mocker):
    """Testuje scenariusz, w którym nie powinno być żadnych dopasowań."""
    mocker.patch('app.logic.db', None)
    
    # Abstrakcyjne, niepasujące dane
    params = {"width": 1, "height": 1, "refresh_rate": 1, "gpu": "fake", "dpr": 1, "ram": 1, "cores": 1}
    matches = find_top_3_matches(**params)
    
    assert len(matches) == 0