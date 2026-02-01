"""
SHARK v18 - Database Module
Obsługa połączeń MongoDB i operacji na bazie danych
"""
import json
import os
import logging
from datetime import datetime
from app.config import (
    MONGODB_AVAILABLE, MONGODB_URI, MONGODB_DB, USE_MONGODB,
    BRAIN_FILE, BRAIN, EXTERNAL_DB, logger
)

# Inicjalizacja kolekcji MongoDB (domyślnie None)
db = None
brain_collection = None
logs_collection = None
verified_models_collection = None
detection_logs_collection = None
external_db_collection = None
static_identifiers_collection = None
android_identifiers_collection = None
accessory_codes_collection = None

def init_mongodb():
    """Inicjalizacja połączenia z MongoDB"""
    global db, brain_collection, logs_collection, verified_models_collection
    global detection_logs_collection, external_db_collection
    global static_identifiers_collection, android_identifiers_collection
    global accessory_codes_collection

    if USE_MONGODB:
        try:
            from pymongo import MongoClient
            from pymongo.errors import ConnectionFailure

            mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            mongo_client.admin.command('ping')
            db = mongo_client[MONGODB_DB]

            # Inicjalizacja wszystkich kolekcji
            brain_collection = db['brain']
            logs_collection = db['logs']
            verified_models_collection = db['verified_models']
            detection_logs_collection = db['detection_logs']
            external_db_collection = db['external_db']
            static_identifiers_collection = db['static_identifiers']
            android_identifiers_collection = db['android_identifiers']
            accessory_codes_collection = db['accessory_codes']

            logger.info("✅ MongoDB connected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            return False
    else:
        logger.info("📁 Using JSON file storage (no MongoDB)")
        return False

def load_data():
    """Load all data from MongoDB (priority) or JSON files (fallback)."""
    import app.config as config
    from app.models.identifiers import STATIC_IDENTIFIERS, ANDROID_IDENTIFIERS, ACCESSORY_CODES

    BRAIN = config.BRAIN
    EXTERNAL_DB = config.EXTERNAL_DB

    # 1. Ładowanie BRAIN
    try:
        if USE_MONGODB:
            brain_data = brain_collection.find_one({'_id': 'brain_v18'})
            if brain_data:
                config.BRAIN.clear()
                config.BRAIN.update(brain_data.get('data', {}))
                logger.info(f"✅ Brain loaded from MongoDB: {len(config.BRAIN)} signatures")
            else:
                config.BRAIN.clear()
                logger.info("No brain data in MongoDB, starting fresh")
        else:
            if os.path.exists(BRAIN_FILE):
                with open(BRAIN_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    config.BRAIN.clear()
                    config.BRAIN.update(data)
                logger.info(f"Brain loaded from file: {len(config.BRAIN)} signatures")
            else:
                config.BRAIN.clear()
    except Exception as e:
        logger.error(f"Error loading brain: {e}")
        config.BRAIN.clear()

    # 2. Ładowanie STATIC_IDENTIFIERS z MongoDB (tylko jeśli istnieje w MongoDB)
    if USE_MONGODB:
        try:
            static_data = static_identifiers_collection.find_one({'_id': 'static_identifiers'})
            if static_data and 'data' in static_data:
                # Merge z oryginalnymi danymi zamiast nadpisywać
                STATIC_IDENTIFIERS.update(static_data['data'])
                logger.info(f"✅ Static Identifiers merged from MongoDB: {len(STATIC_IDENTIFIERS)} models")
        except Exception as e:
            logger.warning(f"⚠️ Error loading Static Identifiers from MongoDB: {e}")

    # 3. Ładowanie ANDROID_IDENTIFIERS z MongoDB (tylko jeśli istnieje w MongoDB)
    if USE_MONGODB:
        try:
            android_data = android_identifiers_collection.find_one({'_id': 'android_identifiers'})
            if android_data and 'data' in android_data:
                # Merge z oryginalnymi danymi zamiast nadpisywać
                ANDROID_IDENTIFIERS.update(android_data['data'])
                logger.info(f"✅ Android Identifiers merged from MongoDB: {len(ANDROID_IDENTIFIERS)} models")
        except Exception as e:
            logger.warning(f"⚠️ Error loading Android Identifiers from MongoDB: {e}")

    # 4. Ładowanie ACCESSORY_CODES z MongoDB (tylko jeśli istnieje w MongoDB)
    if USE_MONGODB:
        try:
            accessory_data = accessory_codes_collection.find_one({'_id': 'accessory_codes'})
            if accessory_data and 'data' in accessory_data:
                # Merge z oryginalnymi danymi zamiast nadpisywać
                ACCESSORY_CODES.update(accessory_data['data'])
                logger.info(f"✅ Accessory Codes merged from MongoDB: {len(ACCESSORY_CODES)} models")
        except Exception as e:
            logger.warning(f"⚠️ Error loading Accessory Codes from MongoDB: {e}")

    # 5. Ładowanie EXTERNAL_DB (Matomo) z MongoDB lub pliku
    config.EXTERNAL_DB.clear()
    config.EXTERNAL_DB.update({**STATIC_IDENTIFIERS, **ANDROID_IDENTIFIERS})

    if USE_MONGODB:
        try:
            external_data = external_db_collection.find_one({'_id': 'external_db'})
            if external_data and 'data' in external_data:
                loaded_db = external_data['data']
                config.EXTERNAL_DB.update(loaded_db)
                logger.info(f"✅ External DB loaded from MongoDB: {len(config.EXTERNAL_DB)} total models")
            else:
                logger.info("No External DB in MongoDB, will try JSON file")
                # Fallback do pliku JSON
                external_db_file = 'shark_external_db.json'
                if os.path.exists(external_db_file):
                    with open(external_db_file, 'r', encoding='utf-8') as f:
                        loaded_db = json.load(f)
                        config.EXTERNAL_DB.update(loaded_db)
                        logger.info(f"✅ External DB loaded from file: {len(config.EXTERNAL_DB)} models")
        except Exception as e:
            logger.error(f"Error loading External DB: {e}")
    else:
        # Tryb JSON - załaduj z pliku
        external_db_file = 'shark_external_db.json'
        if os.path.exists(external_db_file):
            try:
                with open(external_db_file, 'r', encoding='utf-8') as f:
                    loaded_db = json.load(f)
                    config.EXTERNAL_DB.update(loaded_db)
                    logger.info(f"✅ External DB loaded from file: {len(config.EXTERNAL_DB)} models")
            except Exception as e:
                logger.error(f"Error loading external DB: {e}")
        else:
            logger.warning(f"⚠️ External DB file not found. Using default models only ({len(config.EXTERNAL_DB)} models)")
            logger.info("💡 Run 'python setup_database.py' to import 1000+ models from Matomo")

def save_brain():
    """Save brain data to MongoDB or JSON file.

    DEPRECATED: Use save_brain_signature() for atomic writes in multi-worker environments.
    This function is kept for backward compatibility and full brain dumps.
    """
    import app.config as config

    try:
        if USE_MONGODB:
            brain_collection.update_one(
                {'_id': 'brain_v18'},
                {'$set': {'data': config.BRAIN, 'updated_at': datetime.utcnow()}},
                upsert=True
            )
            logger.info(f"Brain saved to MongoDB: {len(config.BRAIN)} signatures")
        else:
            temp = f"{BRAIN_FILE}.tmp"
            with open(temp, 'w', encoding='utf-8') as f:
                json.dump(config.BRAIN, f, indent=2)
            os.replace(temp, BRAIN_FILE)
            logger.info(f"Brain saved to file: {len(config.BRAIN)} signatures")
    except Exception as e:
        logger.error(f"Error saving brain: {e}")

def save_brain_signature(fingerprint, model_data):
    """
    Atomically save a single brain signature to MongoDB.

    This function uses MongoDB's atomic $set operation to update a single signature
    without race conditions. Safe for multi-worker environments (gunicorn -w N).

    Args:
        fingerprint (str): Unique fingerprint key
        model_data (dict): Model data to save

    Returns:
        bool: True if successful, False otherwise

    Example:
        >>> save_brain_signature("w414h896dpr2.0hz60", {
        ...     "model": "iPhone 11",
        ...     "confidence": 95,
        ...     "learned_at": "2026-02-01T12:00:00"
        ... })
    """
    import app.config as config

    try:
        if USE_MONGODB:
            # Atomiczne zapisanie pojedynczej sygnatury
            # Używamy $set z kluczem data.{fingerprint} zamiast nadpisywać cały BRAIN
            result = brain_collection.update_one(
                {'_id': 'brain_v18'},
                {
                    '$set': {
                        f'data.{fingerprint}': model_data,
                        'updated_at': datetime.utcnow()
                    }
                },
                upsert=True
            )

            # Zaktualizuj również lokalną kopię w pamięci
            config.BRAIN[fingerprint] = model_data

            logger.info(f"✅ Brain signature saved atomically: {fingerprint} -> {model_data.get('model', 'Unknown')}")
            return True
        else:
            # Fallback do JSON - używamy blokady pliku
            # Windows: msvcrt, Unix: fcntl
            try:
                if os.name == 'nt':  # Windows
                    import msvcrt
                else:  # Unix/Linux/Mac
                    import fcntl
            except ImportError:
                logger.warning("⚠️ File locking not available on this platform")

            # Zaktualizuj lokalną kopię
            config.BRAIN[fingerprint] = model_data

            # Zapisz z blokadą pliku (ochrona przed race condition)
            temp = f"{BRAIN_FILE}.tmp"
            with open(temp, 'w', encoding='utf-8') as f:
                try:
                    if os.name == 'nt':  # Windows
                        import msvcrt
                        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                        json.dump(config.BRAIN, f, indent=2)
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    else:  # Unix/Linux/Mac
                        import fcntl
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
                        json.dump(config.BRAIN, f, indent=2)
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock
                except (ImportError, OSError):
                    # Fallback bez blokady jeśli nie jest dostępna
                    json.dump(config.BRAIN, f, indent=2)

            os.replace(temp, BRAIN_FILE)

            logger.info(f"✅ Brain signature saved to file: {fingerprint} -> {model_data.get('model', 'Unknown')}")
            return True
    except Exception as e:
        logger.error(f"❌ Error saving brain signature: {e}")
        return False

def load_brain_signature(fingerprint):
    """
    Load a single brain signature from MongoDB.

    Args:
        fingerprint (str): Unique fingerprint key

    Returns:
        dict or None: Model data if found, None otherwise
    """
    import app.config as config

    # Najpierw sprawdź lokalną kopię w pamięci
    if fingerprint in config.BRAIN:
        return config.BRAIN[fingerprint]

    # Jeśli nie ma w pamięci, sprawdź MongoDB
    if USE_MONGODB:
        try:
            brain_data = brain_collection.find_one(
                {'_id': 'brain_v18'},
                {f'data.{fingerprint}': 1}
            )
            if brain_data and 'data' in brain_data and fingerprint in brain_data['data']:
                signature = brain_data['data'][fingerprint]
                # Zaktualizuj lokalną kopię
                config.BRAIN[fingerprint] = signature
                return signature
        except Exception as e:
            logger.error(f"Error loading brain signature: {e}")

    return None

def get_verified_models():
    """Pobierz wszystkie zweryfikowane modele z MongoDB"""
    if USE_MONGODB and verified_models_collection:
        try:
            models = list(verified_models_collection.find({}, {'_id': 0}))
            return models
        except Exception as e:
            logger.error(f"Error fetching verified models: {e}")
            return []
    return []

def add_verified_model(model_data):
    """Dodaj nowy zweryfikowany model do MongoDB"""
    if USE_MONGODB and verified_models_collection:
        try:
            verified_models_collection.insert_one(model_data)
            logger.info(f"Added verified model: {model_data.get('system_name')}")
            return True
        except Exception as e:
            logger.error(f"Error adding verified model: {e}")
            return False
    return False

def update_verified_model(system_name, model_data):
    """Zaktualizuj zweryfikowany model w MongoDB"""
    if USE_MONGODB and verified_models_collection:
        try:
            result = verified_models_collection.update_one(
                {'system_name': system_name},
                {'$set': model_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating verified model: {e}")
            return False
    return False

def delete_verified_model(system_name):
    """Usuń zweryfikowany model z MongoDB"""
    if USE_MONGODB and verified_models_collection:
        try:
            result = verified_models_collection.delete_one({'system_name': system_name})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting verified model: {e}")
            return False
    return False

def log_detection(log_data):
    """Zapisz log detekcji do MongoDB"""
    if USE_MONGODB and detection_logs_collection:
        try:
            detection_logs_collection.insert_one(log_data)
            return True
        except Exception as e:
            logger.error(f"Error logging detection: {e}")
            return False
    return False

def get_detection_logs(limit=100):
    """Pobierz logi detekcji z MongoDB"""
    if USE_MONGODB and detection_logs_collection:
        try:
            logs = list(detection_logs_collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(limit))
            return logs
        except Exception as e:
            logger.error(f"Error fetching detection logs: {e}")
            return []
    return []

def clear_detection_logs():
    """Wyczyść wszystkie logi detekcji"""
    if USE_MONGODB and detection_logs_collection:
        try:
            result = detection_logs_collection.delete_many({})
            logger.info(f"Cleared {result.deleted_count} detection logs")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error clearing detection logs: {e}")
            return 0
    return 0
