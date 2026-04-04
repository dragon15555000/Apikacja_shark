"""
SHARK v18 - Moduł Bazy Danych
Obsługuje połączenie z MongoDB oraz ładowanie/zapisywanie danych.
"""
import json
import os
from datetime import datetime

from .config import logger, USE_MONGODB, MONGODB_URI, MONGODB_DB, BRAIN_FILE
from .models.identifiers import STATIC_IDENTIFIERS, ANDROID_IDENTIFIERS
from .models.accessory_codes import ACCESSORY_CODES

# --- Globalne obiekty bazy danych ---
db = None
brain_collection = None
detection_logs_collection = None
external_db_collection = None
verified_models_collection = None

# --- Globalne słowniki danych ---
BRAIN = {}
EXTERNAL_DB = {}


def init_db_connection():
    """Inicjalizuje połączenie z MongoDB, jeśli jest skonfigurowane."""
    global db, brain_collection, detection_logs_collection, external_db_collection

    if not USE_MONGODB:
        logger.info("💾 Using JSON file storage (MongoDB not configured).")
        return

    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure

        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command('ping')  # Sprawdź połączenie
        db = mongo_client[MONGODB_DB]

        # Inicjalizacja kolekcji
        brain_collection = db['brain']
        detection_logs_collection = db['detection_logs']
        external_db_collection = db['external_db']
        verified_models_collection = db['verified_models']

        logger.info("✅ MongoDB connected successfully.")

    except ImportError:
        logger.error("❌ PyMongo not installed. Cannot use MongoDB.")
        # Zmień flagę, aby reszta aplikacji wiedziała
        from . import config
        config.USE_MONGODB = False
    except ConnectionFailure as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        from . import config
        config.USE_MONGODB = False


def load_data():
    """Ładuje wszystkie dane z MongoDB (priorytet) lub plików JSON (fallback)."""
    global BRAIN, EXTERNAL_DB

    # 1. Ładowanie BRAIN
    try:
        if USE_MONGODB and brain_collection:
            brain_data = brain_collection.find_one({'_id': 'brain_v18'})
            BRAIN = brain_data.get('data', {}) if brain_data else {}
            logger.info(f"🧠 Brain loaded from MongoDB: {len(BRAIN)} signatures")
        elif os.path.exists(BRAIN_FILE):
            with open(BRAIN_FILE, 'r', encoding='utf-8') as f:
                BRAIN = json.load(f)
            logger.info(f"🧠 Brain loaded from file: {len(BRAIN)} signatures")
    except Exception as e:
        logger.error(f"Failed to load BRAIN data: {e}")
        BRAIN = {}

    # 2. Ładowanie EXTERNAL_DB (identyfikatory urządzeń)
    EXTERNAL_DB = {**STATIC_IDENTIFIERS, **ANDROID_IDENTIFIERS}
    logger.info(f"📱 Loaded {len(EXTERNAL_DB)} static device identifiers.")

    # Spróbuj załadować dodatkowe modele z bazy danych lub pliku
    try:
        loaded_from = None
        if USE_MONGODB and external_db_collection:
            external_data = external_db_collection.find_one({'_id': 'external_db'})
            if external_data and 'data' in external_data:
                EXTERNAL_DB.update(external_data['data'])
                loaded_from = "MongoDB"
        else:
            external_db_file = 'shark_external_db.json'
            if os.path.exists(external_db_file):
                with open(external_db_file, 'r', encoding='utf-8') as f:
                    EXTERNAL_DB.update(json.load(f))
                loaded_from = "JSON file"

        if loaded_from:
            logger.info(f"📚 External DB (Matomo, etc.) loaded from {loaded_from}. Total models: {len(EXTERNAL_DB)}")
        else:
            logger.warning("⚠️ External DB not found. Run 'setup_database.py' to import more models.")

    except Exception as e:
        logger.error(f"Failed to load External DB: {e}")


def save_brain_atomic(fingerprint, model_data):
    """
    Atomowo zapisuje pojedynczą sygnaturę do bazy danych.
    Bezpieczne dla środowisk wielowątkowych/wieloprocesowych.
    """
    from .config import MAX_BRAIN_SIGNATURES, MAX_MODELS_PER_SIGNATURE

    # Aktualizuj lokalną kopię
    if fingerprint not in BRAIN and len(BRAIN) >= MAX_BRAIN_SIGNATURES:
        oldest_key = next(iter(BRAIN))
        del BRAIN[oldest_key]
        logger.warning("Brain limit reached, removed oldest signature.")

    if fingerprint not in BRAIN:
        BRAIN[fingerprint] = {}

    if model_data['model'] not in BRAIN[fingerprint] and len(BRAIN[fingerprint]) >= MAX_MODELS_PER_SIGNATURE:
        lfu_model = min(BRAIN[fingerprint], key=BRAIN[fingerprint].get)
        del BRAIN[fingerprint][lfu_model]
        logger.warning(f"Model limit for signature reached, removed LFU model: {lfu_model}")

    BRAIN[fingerprint][model_data['model']] = BRAIN[fingerprint].get(model_data['model'], 0) + 1

    # Zapisz do trwałego magazynu
    try:
        if USE_MONGODB and brain_collection:
            # Użyj atomowej operacji $set w MongoDB
            brain_collection.update_one(
                {'_id': 'brain_v18'},
                {'$set': {f'data.{fingerprint}': BRAIN[fingerprint], 'updated_at': datetime.utcnow()}},
                upsert=True
            )
        else:
            # Zapis atomowy do pliku
            temp_file = f"{BRAIN_FILE}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(BRAIN, f, indent=2)
            os.replace(temp_file, BRAIN_FILE)
        return True
    except Exception as e:
        logger.error(f"CRITICAL: Failed to save brain signature '{fingerprint}': {e}")
        return False