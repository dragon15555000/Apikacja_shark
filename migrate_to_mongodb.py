#!/usr/bin/env python3
"""
Skrypt do migracji danych z shark_brain.json do MongoDB
Uruchom lokalnie: python migrate_to_mongodb.py
"""

import json
import os
from pymongo import MongoClient

# Konfiguracja MongoDB
MONGODB_URI = "mongodb+srv://"
MONGODB_DB = "shark_db"

def migrate_brain_to_mongodb():
    """Migruj dane z shark_brain.json do MongoDB."""

    # Sprawdź czy plik istnieje
    if not os.path.exists('shark_brain.json'):
        print("❌ Plik shark_brain.json nie istnieje!")
        print("ℹ️  Jeśli nie masz jeszcze danych, po prostu zacznij używać MongoDB.")
        return

    # Wczytaj dane z pliku
    with open('shark_brain.json', 'r', encoding='utf-8') as f:
        brain_data = json.load(f)

    print(f"📂 Wczytano {len(brain_data)} sygnatur z pliku")

    # Połącz z MongoDB
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ Połączono z MongoDB")

        db = client[MONGODB_DB]
        brain_collection = db['brain']

        # Zapisz dane
        brain_collection.update_one(
            {'_id': 'brain_v18'},
            {'$set': {'data': brain_data}},
            upsert=True
        )

        print(f"✅ Zmigrowano {len(brain_data)} sygnatur do MongoDB!")
        print(f"📊 Baza: {MONGODB_DB}, Kolekcja: brain")

        # Weryfikacja
        saved_data = brain_collection.find_one({'_id': 'brain_v18'})
        if saved_data:
            print(f"✅ Weryfikacja: {len(saved_data.get('data', {}))} sygnatur w MongoDB")

    except Exception as e:
        print(f"❌ Błąd: {e}")
    finally:
        client.close()

if __name__ == '__main__':
    print("🚀 Migracja danych do MongoDB")
    print("=" * 50)
    migrate_brain_to_mongodb()
    print("=" * 50)
    print("✅ Gotowe!")
