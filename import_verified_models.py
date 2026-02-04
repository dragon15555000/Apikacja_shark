#!/usr/bin/env python3
"""
Skrypt do importu 14 sprawdzonych modeli do MongoDB
Uruchom lokalnie: python import_verified_models.py
"""

import os
from pymongo import MongoClient

# Konfiguracja MongoDB
MONGODB_URI = os.environ.get('MONGODB_URI', "mongodb+srv://")
MONGODB_DB = os.environ.get('MONGODB_DB', 'shark_db')

# 14 sprawdzonych modeli z tabeli
VERIFIED_MODELS = [
    {
        "name": "iPhone 16 Pro Max",
        "system_name": "Apple iPhone 16 Pro Max",
        "w": 440,
        "h": 956,
        "dpr": 3.0,
        "ram": -1,
        "hz": 120,
        "gpu": "apple gpu"
    },
    {
        "name": "iPhone 16 Pro",
        "system_name": "Apple iPhone 16 Pro",
        "w": 402,
        "h": 874,
        "dpr": 3.0,
        "ram": -1,
        "hz": 120,
        "gpu": "apple gpu"
    },
    {
        "name": "iPhone 16",
        "system_name": "Apple iPhone 16",
        "w": 393,
        "h": 852,
        "dpr": 3.0,
        "ram": -1,
        "hz": 60,
        "gpu": "apple gpu"
    },
    {
        "name": "iPhone 15 Pro Max",
        "system_name": "Apple iPhone 15 Pro Max",
        "w": 430,
        "h": 932,
        "dpr": 3.0,
        "ram": -1,
        "hz": 120,
        "gpu": "apple gpu"
    },
    {
        "name": "iPhone 15 Pro",
        "system_name": "Apple iPhone 15 Pro",
        "w": 393,
        "h": 852,
        "dpr": 3.0,
        "ram": -1,
        "hz": 120,
        "gpu": "apple gpu"
    },
    {
        "name": "iPhone 14 Pro",
        "system_name": "Apple iPhone 14 Pro",
        "w": 393,
        "h": 852,
        "dpr": 3.0,
        "ram": -1,
        "hz": 120,
        "gpu": "apple gpu"
    },
    {
        "name": "Samsung S24 Ultra",
        "system_name": "Samsung Galaxy S24 Ultra",
        "w": 384,
        "h": 824,
        "dpr": 3.75,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 750"
    },
    {
        "name": "Samsung S24+",
        "system_name": "Samsung Galaxy S24 Plus",
        "w": 384,
        "h": 832,
        "dpr": 2.8125,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 750"
    },
    {
        "name": "Samsung S24",
        "system_name": "Samsung Galaxy S24",
        "w": 360,
        "h": 780,
        "dpr": 3.0,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 750"
    },
    {
        "name": "Samsung S23 Ultra",
        "system_name": "Samsung Galaxy S23 Ultra",
        "w": 384,
        "h": 824,
        "dpr": 3.75,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 740"
    },
    {
        "name": "Google Pixel 8 Pro",
        "system_name": "Google Pixel 8 Pro",
        "w": 448,
        "h": 998,
        "dpr": 3.0,
        "ram": 8,
        "hz": 120,
        "gpu": "immortalis-g715s mc10"
    },
    {
        "name": "Google Pixel 7 Pro",
        "system_name": "Google Pixel 7 Pro",
        "w": 412,
        "h": 892,
        "dpr": 3.5,
        "ram": 8,
        "hz": 120,
        "gpu": "mali-g710"
    },
    {
        "name": "Xiaomi 14 Pro",
        "system_name": "Xiaomi 14 Pro",
        "w": 412,
        "h": 915,
        "dpr": 3.5,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 750"
    },
    {
        "name": "Xiaomi 13 Ultra",
        "system_name": "Xiaomi 13 Ultra",
        "w": 412,
        "h": 915,
        "dpr": 3.5,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 740"
    }
]

def import_verified_models():
    """Importuj 14 sprawdzonych modeli do MongoDB."""

    print("🚀 Import zweryfikowanych modeli do MongoDB")
    print("=" * 60)

    try:
        # Połącz z MongoDB
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ Połączono z MongoDB")

        db = client[MONGODB_DB]
        verified_models_collection = db['verified_models']

        # Wyczyść istniejące dane (opcjonalnie)
        # verified_models_collection.delete_many({})
        # print("🗑️  Wyczyszczono istniejące modele")

        # Importuj modele
        imported = 0
        skipped = 0

        for model in VERIFIED_MODELS:
            # Sprawdź czy model już istnieje
            existing = verified_models_collection.find_one({'system_name': model['system_name']})

            if existing:
                print(f"⏭️  Pominięto (już istnieje): {model['system_name']}")
                skipped += 1
            else:
                verified_models_collection.insert_one(model)
                print(f"✅ Dodano: {model['system_name']}")
                imported += 1

        print("=" * 60)
        print(f"✅ Import zakończony!")
        print(f"📊 Dodano: {imported} modeli")
        print(f"⏭️  Pominięto: {skipped} modeli")
        print(f"📦 Łącznie w bazie: {verified_models_collection.count_documents({})}")

    except Exception as e:
        print(f"❌ Błąd: {e}")
    finally:
        client.close()

if __name__ == '__main__':
    import_verified_models()
