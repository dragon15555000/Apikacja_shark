# run_matcher.py
import sys
import os

# Dodajemy bieżący katalog do ścieżki, aby Python widział folder 'app'
sys.path.append(os.getcwd())

from app.models.iphone_specs import iphone_database
from app.utils.logic import calculate_weighted_match

def main():
    print("\n--- 🦈 SHARK MATCHING SYSTEM v2.0 (Weighted) ---")
    print("Wpisz parametry poszukiwanego urządzenia.\n")

    try:
        # Pobieranie danych (z domyślnymi wartościami dla testów)
        vp_width = input("Szerokość viewport (np. 393): ") or "393"
        vp_height = input("Wysokość viewport (np. 852): ") or "852"
        target_viewport = f"{vp_width}x{vp_height}"

        target_dpr = int(input("DPR (np. 3): ") or 3)
        target_ram = int(input("Min. RAM GB (np. 8): ") or 8)
        target_hz = int(input("Min. Hz (np. 120): ") or 120)

        # Tworzenie obiektu wymagań
        target_specs = {
            "viewport": target_viewport,
            "dpr": target_dpr,
            "ram": target_ram,
            "hz": target_hz
        }

        print(f"\n🔎 Szukam dopasowań dla: {target_specs}...")

        # Użycie logiki z app/utils/logic.py
        matches = calculate_weighted_match(iphone_database, target_specs)

        print("\n--- 🏆 WYNIKI ---")
        found_perfect = False

        for i, item in enumerate(matches):
            # Wyświetlamy tylko sensowne wyniki (>0 pkt)
            if item['score'] > 0:
                prefix = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "  "
                print(f"{prefix} {item['name']:<20} | Wynik: {item['score']}/100 pkt")

                if item['score'] == 100:
                    found_perfect = True

        if found_perfect:
            print("\n✅ Znaleziono idealne dopasowanie!")
        else:
            print("\n⚠️ Nie znaleziono idealnego modelu (100/100), wyświetlono najbliższe.")

    except ValueError:
        print("❌ Błąd: Podano nieprawidłową liczbę.")
    except Exception as e:
        print(f"❌ Wystąpił błąd: {e}")

if __name__ == "__main__":
    main()