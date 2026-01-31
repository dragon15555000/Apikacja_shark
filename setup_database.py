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
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_matomo_data(url, force_refresh=False):
    """Pobierz dane Matomo z cache lub z sieci."""
    import requests

    local_cache = "matomo_mobiles.yml"

    # Sprawdź czy mamy lokalną kopię i czy nie wymuszono odświeżenia
    if not force_refresh and os.path.exists(local_cache):
        logger.info("📂 Używam lokalnej kopii pliku definicji Matomo.")
        with open(local_cache, 'r', encoding='utf-8') as f:
            return f.read()

    # Jeśli nie, pobierz z sieci
    logger.info("🌐 Pobieranie definicji z GitHub (może to chwilę potrwać)...")
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # Zapisz cache
    with open(local_cache, 'w', encoding='utf-8') as f:
        f.write(response.text)
    logger.info("💾 Zapisano lokalną kopię cache.")

    return response.text

def import_matomo_models(force_refresh=False):
    """Importuj modele z Matomo Device Detector do EXTERNAL_DB."""
    try:
        import requests
        import yaml

        MATOMO_URL = "https://raw.githubusercontent.com/matomo-org/device-detector/master/regexes/device/mobiles.yml"

        yaml_content = fetch_matomo_data(MATOMO_URL, force_refresh=force_refresh)
        devices_data = yaml.safe_load(yaml_content)

        try:
            with open('custom_models.json', 'r', encoding='utf-8') as f:
                custom_data = json.load(f)
            EXTERNAL_DB = {**custom_data.get('iphone_models', {}), **custom_data.get('android_models', {})}
            logger.info("📄 Załadowano niestandardowe modele z pliku custom_models.json.")
        except FileNotFoundError:
            EXTERNAL_DB = {}
            logger.warning("⚠️ Plik 'custom_models.json' nie został znaleziony. Kontynuuję bez niestandardowych modeli.")
        
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

                # Wyciągnij ID urządzenia z regex w sposób odporny na błędy
                match = re.search(r'([\w-]+)', regex)
                if not match:
                    continue
                
                device_id = match.group(1)

                if not device_id or len(device_id) < 2:
                    continue

                # Stwórz pełną nazwę
                full_name = f"{brand} {model_name}" if brand.lower() not in model_name.lower() else model_name

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

    force_update = False
    if check_database_exists():
        logger.info("📁 Baza danych już istnieje: shark_external_db.json")
        response = input("\n❓ Czy chcesz wymusić aktualizację z sieci (zalecane raz na jakiś czas)? (t/n): ")
        if response.lower() == 't':
            force_update = True
        elif response.lower() != 'n':
            logger.info(" entendido como 'n'.")

    if not check_database_exists() or force_update:
        logger.info("🚀 Rozpoczynam import modeli z Matomo Device Detector...")
        result = import_matomo_models(force_refresh=True)
    else:
        logger.info("⏭️  Baza danych jest aktualna. Pomijam import.")
        return

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
