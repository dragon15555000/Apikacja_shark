"""
SHARK v18 - Automatyczny Setup Bazy Danych
===========================================
Skrypt automatycznie importuje ~1000 modeli telefonów z Matomo Device Detector
przy pierwszym uruchomieniu aplikacji.

Uruchomienie:
    python setup_database.py

Autor: SHARK v18 Team
"""

import json
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def import_matomo_models():
    """Importuj modele z Matomo Device Detector do EXTERNAL_DB."""
    try:
        import requests
        import yaml

        MATOMO_URL = "https://raw.githubusercontent.com/matomo-org/device-detector/master/regexes/device/mobiles.yml"

        logger.info("📥 Pobieranie danych z Matomo Device Detector...")
        response = requests.get(MATOMO_URL, timeout=30)
        response.raise_for_status()
        devices_data = yaml.safe_load(response.text)

        # Bazowe identyfikatory (iPhone, Samsung, etc.)
        STATIC_IDENTIFIERS = {
            "iPhone18,1": "iPhone 17 Pro", "iPhone18,2": "iPhone 17 Pro Max",
            "iPhone18,3": "iPhone 17", "iPhone18,4": "iPhone Air",
            "iPhone17,1": "iPhone 16 Pro", "iPhone17,2": "iPhone 16 Pro Max",
            "iPhone17,3": "iPhone 16", "iPhone17,4": "iPhone 16 Plus", "iPhone17,5": "iPhone 16e",
            "iPhone16,1": "iPhone 15 Pro", "iPhone16,2": "iPhone 15 Pro Max",
            "iPhone15,4": "iPhone 15", "iPhone15,5": "iPhone 15 Plus",
            "iPhone15,2": "iPhone 14 Pro", "iPhone15,3": "iPhone 14 Pro Max",
            "iPhone14,7": "iPhone 14", "iPhone14,8": "iPhone 14 Plus",
            "iPhone14,5": "iPhone 13", "iPhone14,2": "iPhone 13 Pro", "iPhone14,3": "iPhone 13 Pro Max",
            "iPhone13,2": "iPhone 12", "iPhone13,3": "iPhone 12 Pro", "iPhone13,4": "iPhone 12 Pro Max",
            "iPhone12,1": "iPhone 11", "iPhone12,3": "iPhone 11 Pro", "iPhone12,5": "iPhone 11 Pro Max"
        }

        ANDROID_IDENTIFIERS = {
            "SM-S928": "Samsung Galaxy S24 Ultra", "SM-S926": "Samsung Galaxy S24+", "SM-S921": "Samsung Galaxy S24",
            "SM-S918": "Samsung Galaxy S23 Ultra", "SM-S916": "Samsung Galaxy S23+", "SM-S911": "Samsung Galaxy S23",
            "SM-S908": "Samsung Galaxy S22 Ultra", "SM-S906": "Samsung Galaxy S22+", "SM-S901": "Samsung Galaxy S22",
            "SM-G998": "Samsung Galaxy S21 Ultra", "SM-G996": "Samsung Galaxy S21+", "SM-G991": "Samsung Galaxy S21",
            "SM-G988": "Samsung Galaxy S20 Ultra", "SM-G986": "Samsung Galaxy S20+", "SM-G981": "Samsung Galaxy S20",
            "SM-A546": "Samsung Galaxy A54", "SM-A536": "Samsung Galaxy A53", "SM-A526": "Samsung Galaxy A52",
            "SM-A346": "Samsung Galaxy A34", "SM-A336": "Samsung Galaxy A33",
            "SM-F946": "Samsung Galaxy Z Fold 5", "SM-F936": "Samsung Galaxy Z Fold 4", "SM-F926": "Samsung Galaxy Z Fold 3",
            "SM-F741": "Samsung Galaxy Z Flip 5", "SM-F721": "Samsung Galaxy Z Flip 4", "SM-F711": "Samsung Galaxy Z Flip 3",
            "Pixel 8 Pro": "Google Pixel 8 Pro", "Pixel 8": "Google Pixel 8",
            "Pixel 7 Pro": "Google Pixel 7 Pro", "Pixel 7": "Google Pixel 7",
            "Pixel 6 Pro": "Google Pixel 6 Pro", "Pixel 6": "Google Pixel 6", "Pixel 5": "Google Pixel 5",
            "2311DRK48C": "Xiaomi 14 Pro", "23117PN0CC": "Xiaomi 14", "2304FPN6DC": "Xiaomi 13 Ultra",
            "2211133C": "Xiaomi 13 Pro", "2211133G": "Xiaomi 13", "2206123SC": "Xiaomi 12 Pro",
            "2201123G": "Xiaomi 12", "M2102K1G": "Xiaomi Mi 11", "M2007J20CG": "Xiaomi Mi 10T Pro",
            "CPH2581": "OnePlus 12", "CPH2449": "OnePlus 11", "NE2213": "OnePlus 10 Pro",
            "LE2123": "OnePlus 9 Pro", "LE2121": "OnePlus 9", "IN2023": "OnePlus 8 Pro", "IN2020": "OnePlus 8",
            "ALN-L29": "Huawei P40 Pro", "ANA-NX9": "Huawei P40", "VOG-L29": "Huawei P30 Pro",
            "ELE-L29": "Huawei P30", "MAR-LX1A": "Huawei P Smart 2019",
        }

        EXTERNAL_DB = {**STATIC_IDENTIFIERS, **ANDROID_IDENTIFIERS}
        new_models = 0
        updated_models = 0

        logger.info("🔄 Przetwarzanie danych Matomo...")

        # Matomo YAML ma strukturę: {brand_name: {models: [...], device: ..., regex: ...}}
        for brand, brand_info in devices_data.items():
            if not isinstance(brand_info, dict):
                continue

            models = brand_info.get('models', [])

            if not isinstance(models, list):
                continue

            for model_entry in models:
                if not isinstance(model_entry, dict):
                    continue

                model_name = model_entry.get('model')
                regex = model_entry.get('regex', '')

                if not model_name or not regex:
                    continue

                # Wyciągnij ID urządzenia z regex
                device_id = regex.replace('[', '').replace(']', '').replace('?', '')
                device_id = device_id.replace('(', '').replace(')', '').replace('|', '')
                device_id = device_id.replace('\\', '').replace('+', '').replace('.', '')
                device_id = device_id.split()[0] if ' ' in device_id else device_id
                device_id = device_id[:20].strip()

                if not device_id or len(device_id) < 2:
                    continue

                # Stwórz pełną nazwę
                full_name = f"{brand} {model_name}" if brand.lower() not in model_name.lower() else model_name

                # Unikaj duplikatów - jeśli klucz już istnieje (case-insensitive), dodaj suffix
                original_device_id = device_id
                counter = 1
                while device_id in EXTERNAL_DB and EXTERNAL_DB[device_id] != full_name:
                    device_id = f"{original_device_id}_{counter}"
                    counter += 1

                if device_id not in EXTERNAL_DB:
                    EXTERNAL_DB[device_id] = full_name
                    new_models += 1
                elif EXTERNAL_DB[device_id] != full_name:
                    EXTERNAL_DB[device_id] = full_name
                    updated_models += 1

        # Zapisz do pliku JSON
        output_file = 'shark_external_db.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(EXTERNAL_DB, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Import zakończony!")
        logger.info(f"   • Nowe modele: {new_models}")
        logger.info(f"   • Zaktualizowane: {updated_models}")
        logger.info(f"   • Łącznie w bazie: {len(EXTERNAL_DB)}")
        logger.info(f"   • Zapisano do: {output_file}")

        return {
            "success": True,
            "new_models": new_models,
            "updated_models": updated_models,
            "total_models": len(EXTERNAL_DB)
        }

    except ImportError as e:
        logger.error(f"❌ Brak wymaganych bibliotek: {e}")
        logger.error("   Zainstaluj: pip install pyyaml requests")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"❌ Błąd podczas importu: {e}")
        return {"success": False, "error": str(e)}

def check_database_exists():
    """Sprawdź czy baza danych już istnieje."""
    return os.path.exists('shark_external_db.json')

def main():
    """Główna funkcja setupu."""
    print("\n" + "="*60)
    print("🦈 SHARK v18 - Automatyczny Setup Bazy Danych")
    print("="*60 + "\n")

    if check_database_exists():
        logger.info("📁 Baza danych już istnieje: shark_external_db.json")
        response = input("\n❓ Czy chcesz zaktualizować bazę? (t/n): ")
        if response.lower() != 't':
            logger.info("⏭️  Pomijam import.")
            return

    logger.info("🚀 Rozpoczynam import modeli z Matomo Device Detector...")
    result = import_matomo_models()

    if result.get("success"):
        print("\n" + "="*60)
        print("✅ SETUP ZAKOŃCZONY POMYŚLNIE!")
        print("="*60)
        print(f"📊 Statystyki:")
        print(f"   • Nowe modele: {result['new_models']}")
        print(f"   • Zaktualizowane: {result['updated_models']}")
        print(f"   • Łącznie: {result['total_models']}")
        print("\n💡 Możesz teraz uruchomić aplikację: python shark_v18_cloud.py")
        print("="*60 + "\n")
    else:
        print("\n" + "="*60)
        print("❌ SETUP NIE POWIÓDŁ SIĘ")
        print("="*60)
        print(f"Błąd: {result.get('error', 'Nieznany błąd')}")
        print("="*60 + "\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
