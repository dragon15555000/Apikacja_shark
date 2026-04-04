"""
SHARK v18 - Test Skuteczności Wykrywania Urządzeń
==================================================

Mierzy procentową skuteczność dla dwóch warstw wykrywania:
  1. UA_EXACT  — parse_device_from_ua() + lookup w EXTERNAL_DB
  2. HEURISTIC — find_top_3_matches() na podstawie fingerprint sprzętowego

Uruchomienie:
    python tests/test_detection_accuracy.py           # pełny raport
    python tests/test_detection_accuracy.py --short   # tylko podsumowanie
    pytest tests/test_detection_accuracy.py -v        # przez pytest (CI)

Interpretacja wyników:
    ✓  — wykryty poprawnie
    ✗  — nie wykryty lub błędna nazwa
    ?  — UA dopasowany ale brak w bazie (zwrócony surowy kod)
"""
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

os.environ.setdefault('MONGODB_URI', '')   # wyłącz Mongo dla testów jednostkowych

from app.logic import parse_device_from_ua, find_top_3_matches
from app.models.identifiers import ANDROID_IDENTIFIERS, STATIC_IDENTIFIERS
from app.models.accessory_codes import ACCESSORY_CODES

# ---------------------------------------------------------------------------
# Tablica urządzeń testowych
# Każdy wpis: (opis, user_agent, oczekiwana_nazwa, fingerprint_dict)
#   fingerprint_dict — dane do testu heurystycznego (może być None)
# ---------------------------------------------------------------------------
DEVICE_TEST_CASES = [
    # ── Samsung Galaxy S series ─────────────────────────────────────────────
    ("Samsung Galaxy S25 Ultra (EU)",
     "Mozilla/5.0 (Linux; Android 15; SM-S938B Build/AP3A.240905.015) AppleWebKit/537.36",
     "Samsung Galaxy S25 Ultra",
     {"width": 384, "height": 824, "refresh_rate": 120, "gpu": "adreno (tm) 830", "dpr": 3.75, "ram": 12, "cores": 12}),

    ("Samsung Galaxy S25+ (EU)",
     "Mozilla/5.0 (Linux; Android 15; SM-S936B Build/AP3A.240905.015) AppleWebKit/537.36",
     "Samsung Galaxy S25+",
     {"width": 384, "height": 832, "refresh_rate": 120, "gpu": "adreno (tm) 830", "dpr": 2.8125, "ram": 12, "cores": 12}),

    ("Samsung Galaxy S25 (EU)",
     "Mozilla/5.0 (Linux; Android 15; SM-S931B Build/AP3A.240905.015) AppleWebKit/537.36",
     "Samsung Galaxy S25",
     {"width": 360, "height": 780, "refresh_rate": 120, "gpu": "adreno (tm) 830", "dpr": 3.0, "ram": 12, "cores": 12}),

    ("Samsung Galaxy S24 Ultra (EU)",
     "Mozilla/5.0 (Linux; Android 14; SM-S928B Build/UP1A.231005.007) AppleWebKit/537.36",
     "Samsung Galaxy S24 Ultra",
     {"width": 384, "height": 824, "refresh_rate": 120, "gpu": "adreno (tm) 750", "dpr": 3.75, "ram": 8, "cores": 8}),

    ("Samsung Galaxy S24+ (EU)",
     "Mozilla/5.0 (Linux; Android 14; SM-S926B Build/UP1A.231005.007) AppleWebKit/537.36",
     "Samsung Galaxy S24+",
     {"width": 384, "height": 832, "refresh_rate": 120, "gpu": "adreno (tm) 750", "dpr": 2.8125, "ram": 8, "cores": 8}),

    ("Samsung Galaxy S24 (EU)",
     "Mozilla/5.0 (Linux; Android 14; SM-S921B Build/UP1A.231005.007) AppleWebKit/537.36",
     "Samsung Galaxy S24",
     {"width": 360, "height": 780, "refresh_rate": 120, "gpu": "adreno (tm) 750", "dpr": 3.0, "ram": 8, "cores": 8}),

    ("Samsung Galaxy S23 Ultra (EU)",
     "Mozilla/5.0 (Linux; Android 13; SM-S918B Build/TP1A.220624.014) AppleWebKit/537.36",
     "Samsung Galaxy S23 Ultra",
     {"width": 384, "height": 824, "refresh_rate": 120, "gpu": "adreno (tm) 740", "dpr": 3.75, "ram": 8, "cores": 8}),

    ("Samsung Galaxy S21 Ultra",
     "Mozilla/5.0 (Linux; Android 11; SM-G998B Build/RP1A.200720.012) AppleWebKit/537.36",
     "Samsung Galaxy S21 Ultra",
     None),

    ("Samsung Galaxy S20 FE",
     "Mozilla/5.0 (Linux; Android 11; SM-G780F Build/RP1A.200720.012) AppleWebKit/537.36",
     "Samsung Galaxy S20 FE",
     None),

    # ── Samsung Galaxy A series ─────────────────────────────────────────────
    ("Samsung Galaxy A55 (EU)",
     "Mozilla/5.0 (Linux; Android 14; SM-A556B Build/AP2A.240405.002) AppleWebKit/537.36",
     "Samsung Galaxy A55",
     {"width": 384, "height": 832, "refresh_rate": 120, "gpu": "xclipse 530", "dpr": 2.8125, "ram": 8, "cores": 8}),

    ("Samsung Galaxy A35 (EU)",
     "Mozilla/5.0 (Linux; Android 14; SM-A356B Build/AP2A.240405.002) AppleWebKit/537.36",
     "Samsung Galaxy A35",
     {"width": 360, "height": 780, "refresh_rate": 120, "gpu": "mali-g68 mc4", "dpr": 3.0, "ram": 6, "cores": 8}),

    ("Samsung Galaxy A54",
     "Mozilla/5.0 (Linux; Android 13; SM-A546B Build/TP1A.220624.014) AppleWebKit/537.36",
     "Samsung Galaxy A54",
     None),

    # ── Samsung Galaxy Z series ─────────────────────────────────────────────
    ("Samsung Galaxy Z Fold 5",
     "Mozilla/5.0 (Linux; Android 13; SM-F946B Build/TP1A.220624.014) AppleWebKit/537.36",
     "Samsung Galaxy Z Fold 5",
     None),

    ("Samsung Galaxy Z Flip 6",
     "Mozilla/5.0 (Linux; Android 14; SM-F751B Build/UP1A.231005.007) AppleWebKit/537.36",
     "Samsung Galaxy Z Flip 6",
     None),

    # ── Google Pixel ────────────────────────────────────────────────────────
    ("Google Pixel 9 Pro XL",
     "Mozilla/5.0 (Linux; Android 15; Pixel 9 Pro XL Build/AP3A.240905.015) AppleWebKit/537.36",
     "Google Pixel 9 Pro XL",
     {"width": 448, "height": 998, "refresh_rate": 120, "gpu": "mali-g715 mc7", "dpr": 3.0, "ram": 16, "cores": 9}),

    ("Google Pixel 9 Pro",
     "Mozilla/5.0 (Linux; Android 15; Pixel 9 Pro Build/AP3A.240905.015) AppleWebKit/537.36",
     "Google Pixel 9 Pro",
     {"width": 412, "height": 915, "refresh_rate": 120, "gpu": "mali-g715 mc7", "dpr": 2.625, "ram": 16, "cores": 9}),

    ("Google Pixel 9",
     "Mozilla/5.0 (Linux; Android 15; Pixel 9 Build/AP3A.240905.015) AppleWebKit/537.36",
     "Google Pixel 9",
     {"width": 412, "height": 915, "refresh_rate": 120, "gpu": "mali-g715 mc7", "dpr": 2.625, "ram": 12, "cores": 9}),

    ("Google Pixel 9 Pro Fold",
     "Mozilla/5.0 (Linux; Android 15; Pixel 9 Pro Fold Build/AP3A.240905.015) AppleWebKit/537.36",
     "Google Pixel 9 Pro Fold",
     None),

    ("Google Pixel 8 Pro",
     "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro Build/AP2A.240405.002) AppleWebKit/537.36",
     "Google Pixel 8 Pro",
     {"width": 448, "height": 998, "refresh_rate": 120, "gpu": "mali-g715 mc7", "dpr": 3.0, "ram": 8, "cores": 9}),

    ("Google Pixel 8",
     "Mozilla/5.0 (Linux; Android 14; Pixel 8 Build/AP2A.240405.002) AppleWebKit/537.36",
     "Google Pixel 8",
     {"width": 412, "height": 892, "refresh_rate": 120, "gpu": "mali-g715 mc7", "dpr": 2.625, "ram": 8, "cores": 9}),

    ("Google Pixel 8a",
     "Mozilla/5.0 (Linux; Android 14; Pixel 8a Build/AP2A.240405.002) AppleWebKit/537.36",
     "Google Pixel 8a",
     {"width": 412, "height": 892, "refresh_rate": 120, "gpu": "mali-g715 mc7", "dpr": 2.625, "ram": 8, "cores": 9}),

    ("Google Pixel 7 Pro",
     "Mozilla/5.0 (Linux; Android 14; Pixel 7 Pro Build/UP1A.231005.007) AppleWebKit/537.36",
     "Google Pixel 7 Pro",
     {"width": 412, "height": 892, "refresh_rate": 120, "gpu": "mali-g710 mc10", "dpr": 3.5, "ram": 8, "cores": 9}),

    ("Google Pixel 7a",
     "Mozilla/5.0 (Linux; Android 14; Pixel 7a Build/UP1A.231005.007) AppleWebKit/537.36",
     "Google Pixel 7a",
     None),

    ("Google Pixel 6a",
     "Mozilla/5.0 (Linux; Android 13; Pixel 6a Build/TP1A.220624.021) AppleWebKit/537.36",
     "Google Pixel 6a",
     None),

    # ── iPhone ──────────────────────────────────────────────────────────────
    ("iPhone 16 Pro Max",
     "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 iPhone17,2",
     "iPhone 16 Pro Max",
     {"width": 440, "height": 956, "refresh_rate": 120, "gpu": "apple a18 pro gpu", "dpr": 3.0, "ram": -1, "cores": 6}),

    ("iPhone 16 Pro",
     "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 iPhone17,1",
     "iPhone 16 Pro",
     {"width": 402, "height": 874, "refresh_rate": 120, "gpu": "apple a18 pro gpu", "dpr": 3.0, "ram": -1, "cores": 6}),

    ("iPhone 16",
     "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 iPhone17,3",
     "iPhone 16",
     {"width": 393, "height": 852, "refresh_rate": 60, "gpu": "apple a18 gpu", "dpr": 3.0, "ram": -1, "cores": 6}),

    ("iPhone 15 Pro Max",
     "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 iPhone16,2",
     "iPhone 15 Pro Max",
     {"width": 430, "height": 932, "refresh_rate": 120, "gpu": "apple a17 pro gpu", "dpr": 3.0, "ram": -1, "cores": 6}),

    ("iPhone 15 Pro",
     "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 iPhone16,1",
     "iPhone 15 Pro",
     {"width": 393, "height": 852, "refresh_rate": 120, "gpu": "apple a17 pro gpu", "dpr": 3.0, "ram": -1, "cores": 6}),

    ("iPhone 13 Pro Max",
     "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 iPhone14,3",
     "iPhone 13 Pro Max",
     {"width": 428, "height": 926, "refresh_rate": 120, "gpu": "apple a15 gpu", "dpr": 3.0, "ram": -1, "cores": 6}),

    ("iPhone 11",
     "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 iPhone12,1",
     "iPhone 11",
     {"width": 414, "height": 896, "refresh_rate": 60, "gpu": "apple a13 gpu", "dpr": 2.0, "ram": -1, "cores": 6}),

    # ── Xiaomi ──────────────────────────────────────────────────────────────
    ("Xiaomi 14 Pro",
     "Mozilla/5.0 (Linux; Android 14; Xiaomi 2311DRK48C Build/UP1A.231005.007) AppleWebKit/537.36",
     "Xiaomi 14 Pro",
     {"width": 412, "height": 915, "refresh_rate": 120, "gpu": "adreno (tm) 750", "dpr": 3.5, "ram": 8, "cores": 8}),

    ("Xiaomi 13 Ultra",
     "Mozilla/5.0 (Linux; Android 13; Xiaomi 2304FPN6DC Build/TP1A.220624.014) AppleWebKit/537.36",
     "Xiaomi 13 Ultra",
     {"width": 412, "height": 915, "refresh_rate": 120, "gpu": "adreno (tm) 740", "dpr": 3.5, "ram": 8, "cores": 8}),

    # ── OnePlus ─────────────────────────────────────────────────────────────
    ("OnePlus 12",
     "Mozilla/5.0 (Linux; Android 14; CPH2581 Build/UP1A.231005.007) AppleWebKit/537.36",
     "OnePlus 12",
     {"width": 412, "height": 919, "refresh_rate": 120, "gpu": "adreno (tm) 750", "dpr": 3.0, "ram": 12, "cores": 8}),

    ("OnePlus 11",
     "Mozilla/5.0 (Linux; Android 13; CPH2449 Build/TP1A.220624.014) AppleWebKit/537.36",
     "OnePlus 11",
     None),

    # ── Motorola ────────────────────────────────────────────────────────────
    ("Motorola Edge 50 Pro",
     "Mozilla/5.0 (Linux; Android 14; motorola edge 50 pro Build/UP1A.231005.007) AppleWebKit/537.36",
     None,   # UA nie ma SM- ani Pixel, więc brak UA_EXACT — tylko heurystyka
     {"width": 412, "height": 915, "refresh_rate": 144, "gpu": "adreno (tm) 735", "dpr": 2.625, "ram": 12, "cores": 8}),

    # ── Realme ──────────────────────────────────────────────────────────────
    ("Realme 12 Pro+",
     "Mozilla/5.0 (Linux; Android 14; RMX3771 Build/UP1A.231005.007) AppleWebKit/537.36",
     "Realme 12 Pro+",
     None),
]

EXTERNAL_DB = {**STATIC_IDENTIFIERS, **ANDROID_IDENTIFIERS}


# ---------------------------------------------------------------------------
# Funkcje pomocnicze
# ---------------------------------------------------------------------------

def check_ua_accuracy(cases, verbose=True):
    """
    Testuje warstwę UA_EXACT:
    parse_device_from_ua(ua) → lookup w EXTERNAL_DB → porównaj z oczekiwaną nazwą.
    Zwraca (ok, skipped, total).
    """
    ok = skipped = 0
    results = []

    for label, ua, expected_name, _ in cases:
        if expected_name is None:
            skipped += 1
            results.append(('~', label, None, None, expected_name))
            continue

        code = parse_device_from_ua(ua)
        found_name = EXTERNAL_DB.get(code) if code else None
        success = found_name == expected_name

        if success:
            ok += 1
        results.append(('✓' if success else '✗', label, code, found_name, expected_name))

    if verbose:
        print("\n── UA_EXACT (parse_device_from_ua + DB lookup) ──────────────────────────────")
        for icon, label, code, found, expected in results:
            if icon == '~':
                print(f"  ~ {label}: pominięty (brak UA_EXACT dla tego modelu)")
            elif icon == '✓':
                print(f"  ✓ {label}: {code!r} → {found!r}")
            else:
                print(f"  ✗ {label}: kod={code!r}, znaleziono={found!r}, oczekiwano={expected!r}")

    total_testable = len(cases) - skipped
    return ok, skipped, total_testable


def check_heuristic_accuracy(cases, verbose=True, top_n=1, db_mock=None):
    """
    Testuje warstwę HEURISTIC:
    find_top_3_matches(fingerprint) → sprawdź czy oczekiwana nazwa jest w top_n wynikach.
    top_n=1 → tylko pierwsze miejsce; top_n=3 → top 3.
    Zwraca (ok, skipped, total).
    """
    ok = skipped = 0
    results = []

    for label, ua, expected_name, fp in cases:
        if fp is None or expected_name is None:
            skipped += 1
            results.append(('~', label, [], expected_name))
            continue

        matches = find_top_3_matches(
            fp["width"], fp["height"], fp["refresh_rate"],
            fp["gpu"], fp["dpr"], fp["ram"], fp["cores"],
            user_agent=ua
        )

        top_names = [m["model"].replace(" (symulacja?)", "") for m in matches[:top_n]]
        success = expected_name in top_names

        if success:
            ok += 1
        results.append(('✓' if success else '✗', label, matches[:3], expected_name))

    if verbose:
        print(f"\n── HEURISTIC (find_top_3_matches, top-{top_n}) ──────────────────────────────")
        for icon, label, matches, expected in results:
            if icon == '~':
                print(f"  ~ {label}: pominięty (brak danych fingerprint)")
            elif icon == '✓':
                top = matches[0] if matches else {}
                print(f"  ✓ {label}: {top.get('model','?')!r} ({top.get('confidence','?')}%)")
            else:
                top3 = ", ".join(f"{m['model']} ({m['confidence']}%)" for m in matches) or "brak"
                print(f"  ✗ {label}: oczekiwano={expected!r}, TOP3=[{top3}]")

    total_testable = len(cases) - skipped
    return ok, skipped, total_testable


def print_summary(ua_ok, ua_skip, ua_total, h1_ok, h1_skip, h1_total, h3_ok, h3_total):
    pct = lambda ok, total: f"{ok*100//total}%" if total > 0 else "N/A"
    print("\n" + "═" * 60)
    print("  RAPORT SKUTECZNOŚCI WYKRYWANIA")
    print("═" * 60)
    print(f"  UA_EXACT   (parse UA + baza):  {ua_ok:3}/{ua_total:3}  {pct(ua_ok, ua_total):>5}")
    print(f"  HEURISTIC  (top-1 fingerprint):{h1_ok:3}/{h1_total:3}  {pct(h1_ok, h1_total):>5}")
    print(f"  HEURISTIC  (top-3 fingerprint):{h3_ok:3}/{h3_total:3}  {pct(h3_ok, h3_total):>5}")
    total_ok = ua_ok + h1_ok
    total = ua_total + h1_total
    print(f"  ŁĄCZNIE    (UA + top-1):       {total_ok:3}/{total:3}  {pct(total_ok, total):>5}")
    print("═" * 60)
    if ua_total > 0 and ua_ok * 100 // ua_total < 80:
        print("  ⚠ Skuteczność UA poniżej 80% — sprawdź ANDROID_IDENTIFIERS")
    if h1_total > 0 and h1_ok * 100 // h1_total < 60:
        print("  ⚠ Skuteczność heurystyki poniżej 60% — sprawdź HEURISTIC_DB / wagi")
    print()


# ---------------------------------------------------------------------------
# Punkt wejścia CLI
# ---------------------------------------------------------------------------

def main():
    short = "--short" in sys.argv
    verbose = not short

    print(f"SHARK v18 — Test skuteczności | {len(DEVICE_TEST_CASES)} urządzeń testowych")
    print(f"EXTERNAL_DB: {len(EXTERNAL_DB)} wpisów | HEURISTIC_DB: zaimportowany")

    ua_ok, ua_skip, ua_total = check_ua_accuracy(DEVICE_TEST_CASES, verbose=verbose)
    h1_ok, h1_skip, h1_total = check_heuristic_accuracy(DEVICE_TEST_CASES, verbose=verbose, top_n=1)
    h3_ok, _, h3_total       = check_heuristic_accuracy(DEVICE_TEST_CASES, verbose=False, top_n=3)

    print_summary(ua_ok, ua_skip, ua_total, h1_ok, h1_skip, h1_total, h3_ok, h3_total)


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Testy pytest — CI/CD
# ---------------------------------------------------------------------------

def test_ua_accuracy_minimum_80_percent():
    """UA_EXACT musi osiągać co najmniej 80% skuteczności."""
    ok, _, total = check_ua_accuracy(DEVICE_TEST_CASES, verbose=False)
    pct = ok * 100 // total
    assert pct >= 80, f"UA accuracy {pct}% poniżej progu 80% ({ok}/{total})"


def test_heuristic_top1_accuracy_minimum_60_percent():
    """Heurystyka top-1 musi osiągać co najmniej 60% skuteczności."""
    ok, _, total = check_heuristic_accuracy(DEVICE_TEST_CASES, verbose=False, top_n=1)
    pct = ok * 100 // total
    assert pct >= 60, f"Heuristic top-1 accuracy {pct}% poniżej progu 60% ({ok}/{total})"


def test_heuristic_top3_accuracy_minimum_75_percent():
    """Heurystyka top-3 musi osiągać co najmniej 75% skuteczności."""
    ok, _, total = check_heuristic_accuracy(DEVICE_TEST_CASES, verbose=False, top_n=3)
    pct = ok * 100 // total
    assert pct >= 75, f"Heuristic top-3 accuracy {pct}% poniżej progu 75% ({ok}/{total})"


def test_samsung_s25_ua_detected():
    assert parse_device_from_ua(
        "Mozilla/5.0 (Linux; Android 15; SM-S938B Build/AP3A) AppleWebKit/537.36"
    ) == "SM-S938"


def test_pixel_9_pro_xl_ua_detected():
    assert parse_device_from_ua(
        "Mozilla/5.0 (Linux; Android 15; Pixel 9 Pro XL Build/AP3A) AppleWebKit/537.36"
    ) == "Pixel 9 Pro XL"


def test_pixel_8a_ua_detected():
    assert parse_device_from_ua(
        "Mozilla/5.0 (Linux; Android 14; Pixel 8a Build/AP2A) AppleWebKit/537.36"
    ) == "Pixel 8a"


def test_iphone_16_pro_ua_detected():
    code = parse_device_from_ua(
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 iPhone17,1"
    )
    assert code == "iPhone17,1"
    assert EXTERNAL_DB.get(code) == "iPhone 16 Pro"


def test_new_models_have_accessory_codes():
    required = [
        "Samsung Galaxy S25 Ultra", "Samsung Galaxy S25+", "Samsung Galaxy S25",
        "Google Pixel 9 Pro", "Google Pixel 9", "Samsung Galaxy A55",
    ]
    missing = [m for m in required if m not in ACCESSORY_CODES]
    assert not missing, f"Brak kodów akcesoriów dla: {missing}"
