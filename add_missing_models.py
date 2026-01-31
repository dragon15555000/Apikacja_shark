#!/usr/bin/env python3
"""Script to add missing verified models to MongoDB"""
import os
from pymongo import MongoClient
from datetime import datetime

# Load .env file
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Load MongoDB credentials
MONGODB_URI = os.environ.get('MONGODB_URI')
MONGODB_DB = os.environ.get('MONGODB_DB', 'shark_db')

if not MONGODB_URI:
    print("ERROR: MONGODB_URI not set!")
    exit(1)

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
verified_models_collection = db['verified_models']

# Missing models to add - Extended database with unique signatures
missing_models = [
    # === APPLE iPhone (2024-2025) ===
    {
        "name": "iPhone 16 Plus",
        "system_name": "Apple iPhone 16 Plus",
        "w": 430,
        "h": 932,
        "dpr": 3.0,
        "ram": -1,
        "hz": 60,
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
        "name": "iPhone 15 Plus",
        "system_name": "Apple iPhone 15 Plus",
        "w": 430,
        "h": 932,
        "dpr": 3.0,
        "ram": -1,
        "hz": 60,
        "gpu": "apple gpu"
    },
    {
        "name": "iPhone 15",
        "system_name": "Apple iPhone 15",
        "w": 393,
        "h": 852,
        "dpr": 3.0,
        "ram": -1,
        "hz": 60,
        "gpu": "apple gpu"
    },
    {
        "name": "iPhone 14 Plus",
        "system_name": "Apple iPhone 14 Plus",
        "w": 428,
        "h": 926,
        "dpr": 3.0,
        "ram": -1,
        "hz": 60,
        "gpu": "apple gpu"
    },
    {
        "name": "iPhone 14",
        "system_name": "Apple iPhone 14",
        "w": 390,
        "h": 844,
        "dpr": 3.0,
        "ram": -1,
        "hz": 60,
        "gpu": "apple gpu"
    },
    {
        "name": "iPhone 13 Pro Max",
        "system_name": "Apple iPhone 13 Pro Max",
        "w": 428,
        "h": 926,
        "dpr": 3.0,
        "ram": -1,
        "hz": 120,
        "gpu": "apple gpu"
    },
    {
        "name": "iPhone 13 Pro",
        "system_name": "Apple iPhone 13 Pro",
        "w": 390,
        "h": 844,
        "dpr": 3.0,
        "ram": -1,
        "hz": 120,
        "gpu": "apple gpu"
    },
    {
        "name": "iPhone 13",
        "system_name": "Apple iPhone 13",
        "w": 390,
        "h": 844,
        "dpr": 3.0,
        "ram": -1,
        "hz": 60,
        "gpu": "apple gpu"
    },

    # === SAMSUNG Galaxy S Series (2024-2023) ===
    {
        "name": "Samsung Galaxy S24 Ultra",
        "system_name": "Samsung Galaxy S24 Ultra",
        "w": 384,
        "h": 824,
        "dpr": 3.75,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 750"
    },
    {
        "name": "Samsung Galaxy S23 Plus",
        "system_name": "Samsung Galaxy S23 Plus",
        "w": 384,
        "h": 832,
        "dpr": 3.0,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 740"
    },
    {
        "name": "Samsung Galaxy S23",
        "system_name": "Samsung Galaxy S23",
        "w": 360,
        "h": 780,
        "dpr": 3.0,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 740"
    },
    {
        "name": "Samsung Galaxy S22 Ultra",
        "system_name": "Samsung Galaxy S22 Ultra",
        "w": 384,
        "h": 824,
        "dpr": 3.0,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 730"
    },
    {
        "name": "Samsung Galaxy S22 Plus",
        "system_name": "Samsung Galaxy S22 Plus",
        "w": 384,
        "h": 832,
        "dpr": 3.0,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 730"
    },
    {
        "name": "Samsung Galaxy S22",
        "system_name": "Samsung Galaxy S22",
        "w": 360,
        "h": 780,
        "dpr": 3.0,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 730"
    },

    # === SAMSUNG Galaxy Z Fold/Flip (Foldables) ===
    {
        "name": "Samsung Galaxy Z Fold 5",
        "system_name": "Samsung Galaxy Z Fold 5",
        "w": 344,
        "h": 748,
        "dpr": 2.625,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 740"
    },
    {
        "name": "Samsung Galaxy Z Flip 5",
        "system_name": "Samsung Galaxy Z Flip 5",
        "w": 412,
        "h": 876,
        "dpr": 2.625,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 740"
    },

    # === GOOGLE Pixel (2024-2023) ===
    {
        "name": "Google Pixel 8",
        "system_name": "Google Pixel 8",
        "w": 412,
        "h": 915,
        "dpr": 2.625,
        "ram": 8,
        "hz": 120,
        "gpu": "immortalis-g715"
    },
    {
        "name": "Google Pixel 7",
        "system_name": "Google Pixel 7",
        "w": 412,
        "h": 915,
        "dpr": 2.625,
        "ram": 8,
        "hz": 90,
        "gpu": "mali-g710"
    },
    {
        "name": "Google Pixel 6 Pro",
        "system_name": "Google Pixel 6 Pro",
        "w": 412,
        "h": 892,
        "dpr": 3.5,
        "ram": 8,
        "hz": 120,
        "gpu": "mali-g78"
    },
    {
        "name": "Google Pixel 6",
        "system_name": "Google Pixel 6",
        "w": 412,
        "h": 915,
        "dpr": 2.625,
        "ram": 8,
        "hz": 90,
        "gpu": "mali-g78"
    },

    # === XIAOMI (2024-2023) ===
    {
        "name": "Xiaomi 14",
        "system_name": "Xiaomi 14",
        "w": 412,
        "h": 915,
        "dpr": 3.0,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 750"
    },
    {
        "name": "Xiaomi 13 Pro",
        "system_name": "Xiaomi 13 Pro",
        "w": 412,
        "h": 915,
        "dpr": 3.5,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 740"
    },
    {
        "name": "Xiaomi 13",
        "system_name": "Xiaomi 13",
        "w": 412,
        "h": 915,
        "dpr": 3.0,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 740"
    },
    {
        "name": "Xiaomi 12 Pro",
        "system_name": "Xiaomi 12 Pro",
        "w": 412,
        "h": 915,
        "dpr": 3.5,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 730"
    },
    {
        "name": "Xiaomi 12",
        "system_name": "Xiaomi 12",
        "w": 360,
        "h": 800,
        "dpr": 3.0,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 730"
    },

    # === OnePlus (2024-2023) ===
    {
        "name": "OnePlus 12",
        "system_name": "OnePlus 12",
        "w": 450,
        "h": 1008,
        "dpr": 3.5,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 750"
    },
    {
        "name": "OnePlus 11",
        "system_name": "OnePlus 11",
        "w": 412,
        "h": 915,
        "dpr": 3.5,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 740"
    },
    {
        "name": "OnePlus 10 Pro",
        "system_name": "OnePlus 10 Pro",
        "w": 412,
        "h": 915,
        "dpr": 3.5,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 730"
    },
    {
        "name": "OnePlus 9 Pro",
        "system_name": "OnePlus 9 Pro",
        "w": 412,
        "h": 892,
        "dpr": 3.5,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 660"
    },

    # === MOTOROLA (2024-2023) ===
    {
        "name": "Motorola Edge 50 Pro",
        "system_name": "Motorola Edge 50 Pro",
        "w": 412,
        "h": 915,
        "dpr": 2.625,
        "ram": 8,
        "hz": 144,
        "gpu": "adreno 735"
    },
    {
        "name": "Motorola Edge 40 Pro",
        "system_name": "Motorola Edge 40 Pro",
        "w": 412,
        "h": 915,
        "dpr": 2.625,
        "ram": 8,
        "hz": 165,
        "gpu": "adreno 740"
    },
    {
        "name": "Motorola Moto G84",
        "system_name": "Motorola Moto G84",
        "w": 412,
        "h": 915,
        "dpr": 2.4,
        "ram": 8,
        "hz": 120,
        "gpu": "adreno 619"
    }
]

# Add models
added = 0
for model in missing_models:
    # Check if already exists
    existing = verified_models_collection.find_one({'system_name': model['system_name']})
    if existing:
        print(f"⚠️  {model['system_name']} already exists - skipping")
        continue

    # Insert
    verified_models_collection.insert_one(model)
    print(f"✅ Added: {model['system_name']}")
    added += 1

print(f"\n✅ Added {added} new models!")
print(f"📊 Total models in database: {verified_models_collection.count_documents({})}")
