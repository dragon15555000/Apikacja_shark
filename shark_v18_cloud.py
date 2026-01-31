# SHARK v18.18 - MongoDB collection fix + cache clear
import json
import logging
import os
import re
from collections import deque
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Ĺadowanie zmiennych Ĺ›rodowiskowych z pliku .env (jeĹ›li istnieje)
if os.path.exists('.env'):
    print("đź“„ Loading environment variables from .env file...")
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
    print("âś… Environment variables loaded from .env")

# MongoDB (opcjonalnie)
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("âš ď¸Ź PyMongo not installed. Using JSON file storage.")

# --- KONFIGURACJA ---
LOG_FILE = 'shark_logs_v18.csv'
BRAIN_FILE = 'shark_brain_v18.json'
MAX_BRAIN_SIGNATURES = 10000
MAX_MODELS_PER_SIGNATURE = 5

RECENT_LOGS = deque(maxlen=20)
BRAIN = {}
EXTERNAL_DB = {}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# --- MONGODB SETUP (jeĹ›li dostÄ™pne) ---
MONGODB_URI = os.environ.get('MONGODB_URI', None)
MONGODB_DB = os.environ.get('MONGODB_DB', 'shark_db')
USE_MONGODB = MONGODB_AVAILABLE and MONGODB_URI

# Inicjalizacja kolekcji MongoDB (domyĹ›lnie None)
db = None
brain_collection = None
logs_collection = None
verified_models_collection = None
detection_logs_collection = None
external_db_collection = None
static_identifiers_collection = None
android_identifiers_collection = None
accessory_codes_collection = None

if USE_MONGODB:
    try:
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command('ping')
        db = mongo_client[MONGODB_DB]
        brain_collection = db['brain']
        logs_collection = db['logs']
        verified_models_collection = db['verified_models']
        detection_logs_collection = db['detection_logs']
        # NOWE: Kolekcje dla wszystkich sĹ‚ownikĂłw
        external_db_collection = db['external_db']
        static_identifiers_collection = db['static_identifiers']
        android_identifiers_collection = db['android_identifiers']
        accessory_codes_collection = db['accessory_codes']
        logger.info("âś… MongoDB connected successfully")
    except Exception as e:
        logger.error(f"âťŚ MongoDB connection failed: {e}")
        USE_MONGODB = False
        # Kolekcje juĹĽ sÄ… ustawione na None globalnie
else:
    logger.info("đź“ Using JSON file storage (no MongoDB)")
    # Kolekcje juĹĽ sÄ… ustawione na None globalnie

# --- IDENTYFIKATORY URZÄ„DZEĹ ---
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

ACCESSORY_CODES = {
    "iPhone 17 Pro Max": {"screen": "A1U1", "case": "A1U2"}, "iPhone 17 Pro": {"screen": "A2U1", "case": "A2U2"},
    "iPhone 17": {"screen": "A3U1", "case": "A3U2"}, "iPhone Air": {"screen": "A4U1", "case": "A4U2"},
    "iPhone 16 Pro Max": {"screen": "B1U1", "case": "B1U2"}, "iPhone 16 Pro": {"screen": "B2U1", "case": "B2U2"},
    "iPhone 16": {"screen": "B3U1", "case": "B3U2"}, "iPhone 16 Plus": {"screen": "B4U1", "case": "B4U2"},
    "iPhone 16e": {"screen": "B5U1", "case": "B5U2"},
    "iPhone 15 Pro Max": {"screen": "C1U1", "case": "C1U2"}, "iPhone 15 Pro": {"screen": "C2U1", "case": "C2U2"},
    "iPhone 15": {"screen": "C3U1", "case": "C3U2"}, "iPhone 15 Plus": {"screen": "C4U1", "case": "C4U2"},
    "iPhone 14 Pro Max": {"screen": "D1U1", "case": "D1U2"}, "iPhone 14 Pro": {"screen": "D2U1", "case": "D2U2"},
    "iPhone 14": {"screen": "D3U1", "case": "D3U2"}, "iPhone 14 Plus": {"screen": "D4U1", "case": "D4U2"},
    "iPhone 13 Pro Max": {"screen": "E1U1", "case": "E1U2"}, "iPhone 13 Pro": {"screen": "E2U1", "case": "E2U2"},
    "iPhone 13": {"screen": "E3U1", "case": "E3U2"},
    "iPhone 12 Pro Max": {"screen": "F1U1", "case": "F1U2"}, "iPhone 12 Pro": {"screen": "F2U1", "case": "F2U2"},
    "iPhone 12": {"screen": "F3U1", "case": "F3U2"},
    "iPhone 11 Pro Max": {"screen": "G1U1", "case": "G1U2"}, "iPhone 11 Pro": {"screen": "G2U1", "case": "G2U2"},
    "iPhone 11": {"screen": "G3U1", "case": "G3U2"},
    "Samsung Galaxy S24 Ultra": {"screen": "SA1U1", "case": "SA1U2"}, "Samsung Galaxy S24+": {"screen": "SA2U1", "case": "SA2U2"},
    "Samsung Galaxy S24": {"screen": "SA3U1", "case": "SA3U2"}, "Samsung Galaxy S23 Ultra": {"screen": "SB1U1", "case": "SB1U2"},
    "Samsung Galaxy S23+": {"screen": "SB2U1", "case": "SB2U2"}, "Samsung Galaxy S23": {"screen": "SB3U1", "case": "SB3U2"},
    "Samsung Galaxy S22 Ultra": {"screen": "SC1U1", "case": "SC1U2"}, "Samsung Galaxy S22+": {"screen": "SC2U1", "case": "SC2U2"},
    "Samsung Galaxy S22": {"screen": "SC3U1", "case": "SC3U2"}, "Samsung Galaxy S21 Ultra": {"screen": "SD1U1", "case": "SD1U2"},
    "Samsung Galaxy S21+": {"screen": "SD2U1", "case": "SD2U2"}, "Samsung Galaxy S21": {"screen": "SD3U1", "case": "SD3U2"},
    "Samsung Galaxy S20 Ultra": {"screen": "SE1U1", "case": "SE1U2"}, "Samsung Galaxy S20+": {"screen": "SE2U1", "case": "SE2U2"},
    "Samsung Galaxy S20": {"screen": "SE3U1", "case": "SE3U2"},
    "Samsung Galaxy A54": {"screen": "AA1U1", "case": "AA1U2"}, "Samsung Galaxy A53": {"screen": "AA2U1", "case": "AA2U2"},
    "Samsung Galaxy A52": {"screen": "AA3U1", "case": "AA3U2"}, "Samsung Galaxy A34": {"screen": "AA4U1", "case": "AA4U2"},
    "Samsung Galaxy A33": {"screen": "AA5U1", "case": "AA5U2"},
    "Samsung Galaxy Z Fold 5": {"screen": "ZF1U1", "case": "ZF1U2"}, "Samsung Galaxy Z Fold 4": {"screen": "ZF2U1", "case": "ZF2U2"},
    "Samsung Galaxy Z Fold 3": {"screen": "ZF3U1", "case": "ZF3U2"}, "Samsung Galaxy Z Flip 5": {"screen": "ZP1U1", "case": "ZP1U2"},
    "Samsung Galaxy Z Flip 4": {"screen": "ZP2U1", "case": "ZP2U2"}, "Samsung Galaxy Z Flip 3": {"screen": "ZP3U1", "case": "ZP3U2"},
    "Google Pixel 8 Pro": {"screen": "GP1U1", "case": "GP1U2"}, "Google Pixel 8": {"screen": "GP2U1", "case": "GP2U2"},
    "Google Pixel 7 Pro": {"screen": "GP3U1", "case": "GP3U2"}, "Google Pixel 7": {"screen": "GP4U1", "case": "GP4U2"},
    "Google Pixel 6 Pro": {"screen": "GP5U1", "case": "GP5U2"}, "Google Pixel 6": {"screen": "GP6U1", "case": "GP6U2"},
    "Google Pixel 5": {"screen": "GP7U1", "case": "GP7U2"},
    "Xiaomi 14 Pro": {"screen": "XM1U1", "case": "XM1U2"}, "Xiaomi 14": {"screen": "XM2U1", "case": "XM2U2"},
    "Xiaomi 13 Ultra": {"screen": "XM3U1", "case": "XM3U2"}, "Xiaomi 13 Pro": {"screen": "XM4U1", "case": "XM4U2"},
    "Xiaomi 13": {"screen": "XM5U1", "case": "XM5U2"}, "Xiaomi 12 Pro": {"screen": "XM6U1", "case": "XM6U2"},
    "Xiaomi 12": {"screen": "XM7U1", "case": "XM7U2"}, "Xiaomi Mi 11": {"screen": "XM8U1", "case": "XM8U2"},
    "Xiaomi Mi 10T Pro": {"screen": "XM9U1", "case": "XM9U2"},
    "OnePlus 12": {"screen": "OP1U1", "case": "OP1U2"}, "OnePlus 11": {"screen": "OP2U1", "case": "OP2U2"},
    "OnePlus 10 Pro": {"screen": "OP3U1", "case": "OP3U2"}, "OnePlus 9 Pro": {"screen": "OP4U1", "case": "OP4U2"},
    "OnePlus 9": {"screen": "OP5U1", "case": "OP5U2"}, "OnePlus 8 Pro": {"screen": "OP6U1", "case": "OP6U2"},
    "OnePlus 8": {"screen": "OP7U1", "case": "OP7U2"},
    "Huawei P40 Pro": {"screen": "HW1U1", "case": "HW1U2"}, "Huawei P40": {"screen": "HW2U1", "case": "HW2U2"},
    "Huawei P30 Pro": {"screen": "HW3U1", "case": "HW3U2"}, "Huawei P30": {"screen": "HW4U1", "case": "HW4U2"},
    "Huawei P Smart 2019": {"screen": "HW5U1", "case": "HW5U2"},
}

# Baza heurystyczna - SPRAWDZONE PARAMETRY z rzeczywistych urzÄ…dzeĹ„
HEURISTIC_DB = {
    # iPhone - SPRAWDZONE (z JSON)
    "iPhone 16 Pro Max": {"w": 440, "h": 956, "hz": 120, "gpu": "apple gpu", "dpr": 3.0, "ram": -1},
    "iPhone 16 Pro": {"w": 402, "h": 874, "hz": 120, "gpu": "apple gpu", "dpr": 3.0, "ram": -1},
    "iPhone 16": {"w": 393, "h": 852, "hz": 60, "gpu": "apple gpu", "dpr": 3.0, "ram": -1},
    "iPhone 15 Pro Max": {"w": 430, "h": 932, "hz": 120, "gpu": "apple gpu", "dpr": 3.0, "ram": -1},
    "iPhone 15 Pro": {"w": 393, "h": 852, "hz": 120, "gpu": "apple gpu", "dpr": 3.0, "ram": -1},
    "iPhone 14 Pro": {"w": 393, "h": 852, "hz": 120, "gpu": "apple gpu", "dpr": 3.0, "ram": -1},
    # Samsung - SPRAWDZONE (z JSON)
    "Samsung Galaxy S24 Ultra": {"w": 384, "h": 824, "hz": 120, "gpu": "adreno 750", "dpr": 3.75, "ram": 8},
    "Samsung Galaxy S24 Plus": {"w": 384, "h": 832, "hz": 120, "gpu": "adreno 750", "dpr": 3.75, "ram": 8},
    "Samsung Galaxy S24": {"w": 360, "h": 780, "hz": 120, "gpu": "adreno 750", "dpr": 3.0, "ram": 8},
    "Samsung Galaxy S23 Ultra": {"w": 384, "h": 824, "hz": 120, "gpu": "adreno 740", "dpr": 3.75, "ram": 8},
    # Google Pixel - SPRAWDZONE (z JSON)
    "Google Pixel 8 Pro": {"w": 448, "h": 998, "hz": 120, "gpu": "mali-g715", "dpr": 3.0, "ram": 8},
    "Google Pixel 7 Pro": {"w": 412, "h": 892, "hz": 120, "gpu": "mali-g710", "dpr": 3.5, "ram": 8},
    # Xiaomi - SPRAWDZONE (z JSON)
    "Xiaomi 14 Pro": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno 750", "dpr": 3.5, "ram": 8},
    "Xiaomi 13 Ultra": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno 740", "dpr": 3.5, "ram": 8},
    # Motorola - dodatkowe modele
    "Motorola Edge 50 Pro": {"w": 412, "h": 915, "hz": 144, "gpu": "adreno 735", "dpr": 2.625, "ram": 12},
    "Motorola Edge 50": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno 732", "dpr": 2.625, "ram": 8},
    "Motorola Edge 40 Pro": {"w": 412, "h": 915, "hz": 165, "gpu": "adreno 740", "dpr": 2.625, "ram": 12},
    "Motorola Moto G84": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno 619", "dpr": 2.4, "ram": 8},
}

def load_data():
    """Load all data from MongoDB (priority) or JSON files (fallback)."""
    global BRAIN, EXTERNAL_DB, STATIC_IDENTIFIERS, ANDROID_IDENTIFIERS, ACCESSORY_CODES

    # 1. Ĺadowanie BRAIN
    try:
        if USE_MONGODB:
            brain_data = brain_collection.find_one({'_id': 'brain_v18'})
            if brain_data:
                BRAIN = brain_data.get('data', {})
                logger.info(f"âś… Brain loaded from MongoDB: {len(BRAIN)} signatures")
            else:
                BRAIN = {}
                logger.info("No brain data in MongoDB, starting fresh")
        else:
            if os.path.exists(BRAIN_FILE):
                with open(BRAIN_FILE, 'r', encoding='utf-8') as f:
                    BRAIN = json.load(f)
                logger.info(f"Brain loaded from file: {len(BRAIN)} signatures")
            else:
                BRAIN = {}
    except Exception as e:
        logger.error(f"Error loading brain: {e}")
        BRAIN = {}

    # 2. Ĺadowanie STATIC_IDENTIFIERS z MongoDB (tylko jeĹ›li istnieje w MongoDB)
    if USE_MONGODB:
        try:
            static_data = static_identifiers_collection.find_one({'_id': 'static_identifiers'})
            if static_data and 'data' in static_data:
                # Merge z oryginalnymi danymi zamiast nadpisywaÄ‡
                STATIC_IDENTIFIERS.update(static_data['data'])
                logger.info(f"âś… Static Identifiers merged from MongoDB: {len(STATIC_IDENTIFIERS)} models")
        except Exception as e:
            logger.warning(f"âš ď¸Ź Error loading Static Identifiers from MongoDB: {e}")

    # 3. Ĺadowanie ANDROID_IDENTIFIERS z MongoDB (tylko jeĹ›li istnieje w MongoDB)
    if USE_MONGODB:
        try:
            android_data = android_identifiers_collection.find_one({'_id': 'android_identifiers'})
            if android_data and 'data' in android_data:
                # Merge z oryginalnymi danymi zamiast nadpisywaÄ‡
                ANDROID_IDENTIFIERS.update(android_data['data'])
                logger.info(f"âś… Android Identifiers merged from MongoDB: {len(ANDROID_IDENTIFIERS)} models")
        except Exception as e:
            logger.warning(f"âš ď¸Ź Error loading Android Identifiers from MongoDB: {e}")

    # 4. Ĺadowanie ACCESSORY_CODES z MongoDB (tylko jeĹ›li istnieje w MongoDB)
    if USE_MONGODB:
        try:
            accessory_data = accessory_codes_collection.find_one({'_id': 'accessory_codes'})
            if accessory_data and 'data' in accessory_data:
                # Merge z oryginalnymi danymi zamiast nadpisywaÄ‡
                ACCESSORY_CODES.update(accessory_data['data'])
                logger.info(f"âś… Accessory Codes merged from MongoDB: {len(ACCESSORY_CODES)} models")
        except Exception as e:
            logger.warning(f"âš ď¸Ź Error loading Accessory Codes from MongoDB: {e}")

    # 5. Ĺadowanie EXTERNAL_DB (Matomo) z MongoDB lub pliku
    EXTERNAL_DB = {**STATIC_IDENTIFIERS, **ANDROID_IDENTIFIERS}

    if USE_MONGODB:
        try:
            external_data = external_db_collection.find_one({'_id': 'external_db'})
            if external_data and 'data' in external_data:
                loaded_db = external_data['data']
                EXTERNAL_DB.update(loaded_db)
                logger.info(f"âś… External DB loaded from MongoDB: {len(EXTERNAL_DB)} total models")
            else:
                logger.info("No External DB in MongoDB, will try JSON file")
                # Fallback do pliku JSON
                external_db_file = 'shark_external_db.json'
                if os.path.exists(external_db_file):
                    with open(external_db_file, 'r', encoding='utf-8') as f:
                        loaded_db = json.load(f)
                        EXTERNAL_DB.update(loaded_db)
                        logger.info(f"âś… External DB loaded from file: {len(EXTERNAL_DB)} models")
        except Exception as e:
            logger.error(f"Error loading External DB: {e}")
    else:
        # Tryb JSON - zaĹ‚aduj z pliku
        external_db_file = 'shark_external_db.json'
        if os.path.exists(external_db_file):
            try:
                with open(external_db_file, 'r', encoding='utf-8') as f:
                    loaded_db = json.load(f)
                    EXTERNAL_DB.update(loaded_db)
                    logger.info(f"âś… External DB loaded from file: {len(EXTERNAL_DB)} models")
            except Exception as e:
                logger.error(f"Error loading external DB: {e}")
        else:
            logger.warning(f"âš ď¸Ź External DB file not found. Using default models only ({len(EXTERNAL_DB)} models)")
            logger.info("đź’ˇ Run 'python setup_database.py' to import 1000+ models from Matomo")

def save_brain():
    """Save brain data to MongoDB or JSON file."""
    try:
        if USE_MONGODB:
            brain_collection.update_one(
                {'_id': 'brain_v18'},
                {'$set': {'data': BRAIN, 'updated_at': datetime.utcnow()}},
                upsert=True
            )
            logger.info(f"Brain saved to MongoDB: {len(BRAIN)} signatures")
        else:
            temp = f"{BRAIN_FILE}.tmp"
            with open(temp, 'w', encoding='utf-8') as f:
                json.dump(BRAIN, f, indent=2)
            os.replace(temp, BRAIN_FILE)
            logger.info(f"Brain saved to file: {len(BRAIN)} signatures")
    except Exception as e:
        logger.error(f"Error saving brain: {e}")

def parse_device_from_ua(ua):
    """Parse device identifier from User-Agent string (iOS and Android)"""
    if not ua or not isinstance(ua, str):
        return None
    if len(ua) > 1000:
        ua = ua[:1000]
    try:
        match = re.search(r'iPhone(\d+,\d+)', ua)
        if match:
            return "iPhone" + match.group(1)
        match_ipad = re.search(r'iPad(\d+,\d+)', ua)
        if match_ipad:
            return "iPad" + match_ipad.group(1)
        match_samsung = re.search(r'(SM-[A-Z]\d{3}[A-Z]?)', ua)
        if match_samsung:
            return match_samsung.group(1)[:7]
        match_pixel = re.search(r'(Pixel \d+(?:\s+Pro)?)', ua)
        if match_pixel:
            return match_pixel.group(1)
        match_xiaomi = re.search(r'Build/([A-Z0-9]{10,})', ua)
        if match_xiaomi and 'Xiaomi' in ua:
            return match_xiaomi.group(1)[:12]
        match_oneplus = re.search(r'((?:CPH|LE|IN|NE)\d{4})', ua)
        if match_oneplus:
            return match_oneplus.group(1)
        match_huawei = re.search(r'([A-Z]{3}-[A-Z0-9]{3,5})', ua)
        if match_huawei and ('HUAWEI' in ua.upper() or 'HONOR' in ua.upper()):
            return match_huawei.group(1)
        # Motorola - wzorce: XT2xxx, XT21xx, moto g, edge, razr
        match_motorola = re.search(r'(XT\d{4})', ua)
        if match_motorola:
            return match_motorola.group(1)
        if 'motorola' in ua.lower() or 'moto' in ua.lower():
            # PrĂłbuj wyciÄ…gnÄ…Ä‡ nazwÄ™ modelu
            match_moto_name = re.search(r'(moto [a-z0-9 ]+|edge [a-z0-9 ]+|razr [a-z0-9 ]+)', ua.lower())
            if match_moto_name:
                return match_moto_name.group(1).strip()
    except Exception as e:
        logger.error(f"Error parsing UA: {e}")
    return None

def find_top_3_matches(width, height, refresh_rate, gpu, dpr, ram, cores):
    """
    Find top 3 best matching models using Weighted Scoring Algorithm with OS Segmentation.

    TESTOWANIE:
    - Chrome DevTools (F12) â†’ Tryb responsywny â†’ Edit â†’ Dodaj wĹ‚asne urzÄ…dzenie
    - Ustaw User Agent, DPR, viewport - moĹĽesz symulowaÄ‡ dowolny telefon
    - SprawdĹş logi w konsoli serwera, aby zobaczyÄ‡ szczegĂłĹ‚y punktacji
    """
    matches = []
    gpu_lower = gpu.lower()

    # OS Segmentation - wykryj iOS vs Android
    is_ios = "apple" in gpu_lower or ram == -1

    # Wykryj symulacjÄ™/emulacjÄ™ (GPU komputera zamiast telefonu)
    is_simulation = any(keyword in gpu_lower for keyword in ["intel", "nvidia", "amd", "angle", "swiftshader", "mesa"])

    logger.info(f"đź”Ť Weighted Scoring - OS: {'iOS' if is_ios else 'Android'}, DPR: {dpr}, RAM: {ram}, GPU: {gpu}")
    if is_simulation:
        logger.warning(f"âš ď¸Ź SYMULACJA WYKRYTA! GPU komputera: {gpu[:50]}")

    # Pobierz zweryfikowane modele z MongoDB (jeśli dostępne)
    verified_models = {}
    if USE_MONGODB and verified_models_collection is not None:
        try:
            models_cursor = verified_models_collection.find({})
            for model_doc in models_cursor:
                name = model_doc.get('system_name') or model_doc.get('name')
                if name:
                    verified_models[name] = {
                        "w": model_doc.get('w'),
                        "h": model_doc.get('h'),
                        "dpr": model_doc.get('dpr'),
                        "ram": model_doc.get('ram', -1),
                        "hz": model_doc.get('hz'),
                        "gpu": model_doc.get('gpu', '').lower()
                    }
        except Exception as e:
            logger.warning(f"Error loading verified models: {e}")

    # Połącz HEURISTIC_DB z verified_models (verified ma priorytet)
    all_models = {**HEURISTIC_DB, **verified_models}

    logger.info(f"🔍 Searching in {len(all_models)} models ({len(HEURISTIC_DB)} heuristic + {len(verified_models)} verified)")

    for model_name, specs in all_models.items():
        score = 0
        reasons = []

        # 1. GPU (Waga: 40 Android / 0 iOS)
        # UWAGA: Normalizacja GPU - rĂłĹĽne przeglÄ…darki zwracajÄ… rĂłĹĽne formaty
        # "Adreno (TM) 740" vs "Adreno 740 @ 680 MHz" - szukamy czÄ™Ĺ›ci wspĂłlnej
        if not is_ios and specs["gpu"] and gpu_lower:
            spec_gpu_lower = specs["gpu"].lower()
            # WyciÄ…gnij kluczowe sĹ‚owa (np. "adreno 740" â†’ ["adreno", "740"])
            spec_gpu_parts = spec_gpu_lower.replace("(tm)", "").replace("@", " ").split()
            # SprawdĹş czy wszystkie kluczowe czÄ™Ĺ›ci sÄ… w GPU uĹĽytkownika
            if all(part in gpu_lower for part in spec_gpu_parts if len(part) > 2):
                score += 40
                reasons.append(f"GPU: {specs['gpu']}")
            # Fallback: prosta zawartoĹ›Ä‡
            elif spec_gpu_lower in gpu_lower:
                score += 40
                reasons.append(f"GPU: {specs['gpu']}")

        # 2. Viewport Width (Waga: 50 iOS / 20 Android)
        if specs["w"] == width:
            score += 50 if is_ios else 20
            reasons.append(f"SzerokoĹ›Ä‡: {specs['w']}px")
        elif not is_ios and abs(specs["w"] - width) <= 40:
            score += 10
            reasons.append(f"SzerokoĹ›Ä‡ ~{specs['w']}px")

        # 3. Viewport Height (Waga: 30 iOS / 10 Android) - z tolerancjÄ… na pasek adresu
        if specs["h"] == height:
            score += 30 if is_ios else 10
            reasons.append(f"WysokoĹ›Ä‡: {specs['h']}px")
        elif height < specs["h"] and height > (specs["h"] - 160):
            # Tolerancja na pasek adresu (100-160px)
            score += 25 if is_ios else 8
            reasons.append(f"WysokoĹ›Ä‡ ~{specs['h']}px (pasek adresu)")

        # 4. DPR (Waga: 20 iOS / 25 Android) - KLUCZOWE!
        if abs(specs["dpr"] - dpr) < 0.1:
            score += 20 if is_ios else 25
            reasons.append(f"DPR: {specs['dpr']}x")
        elif abs(specs["dpr"] - dpr) < 0.5:
            score += 10
            reasons.append(f"DPR ~{specs['dpr']}x")

        # 5. Hz (Waga: 5 bonus / -10 kara) - RozrĂłĹĽnia Pro/Base
        if specs["hz"] and refresh_rate:
            if abs(specs["hz"] - refresh_rate) < 5:
                score += 5
                reasons.append(f"Hz: {specs['hz']}Hz")
            else:
                score -= 10  # Kara za niezgodnoĹ›Ä‡ (np. iPhone 16 vs 15 Pro)

        # 6. RAM (Waga: 5 Android / 0 iOS) - sĹ‚aby sygnaĹ‚
        # UWAGA: navigator.deviceMemory zaokrÄ…gla wartoĹ›ci (12GB â†’ 8GB)
        if not is_ios and ram > 0 and specs["ram"] > 0:
            # UĹĽyj >= zamiast == bo Chrome zaokrÄ…gla RAM w dĂłĹ‚
            if ram >= specs["ram"] or abs(specs["ram"] - ram) <= 2:
                score += 5
                reasons.append(f"RAM: ~{specs['ram']}GB")

        if score > 0:
            # JeĹ›li wykryto symulacjÄ™, dodaj flagÄ™
            if is_simulation and score >= 100:
                # Idealny match ale GPU komputera = prawdopodobnie symulacja
                matches.append({
                    "model": model_name + " (symulacja?)",
                    "confidence": min(score, 100),
                    "reasons": reasons + ["âš ď¸Ź GPU komputera wykryty"],
                    "raw_score": score,
                    "is_simulation": True
                })
            else:
                # Normalne rozpoznanie
                matches.append({
                    "model": model_name,
                    "confidence": min(score, 100),
                    "reasons": reasons,
                    "raw_score": score,
                    "is_simulation": False
                })

    # Sortuj po confidence i zwrĂłÄ‡ top 3
    matches.sort(key=lambda x: x["confidence"], reverse=True)

    # Loguj top 3 z PEĹNYMI szczegĂłĹ‚ami punktacji
    logger.info(f"đźŹ† TOP 3 MATCHES (z {len(matches)} kandydatĂłw):")
    for i, match in enumerate(matches[:3], 1):
        reasons_str = ', '.join(match['reasons']) if match['reasons'] else 'brak dopasowaĹ„'
        logger.info(f"  #{i}: {match['model']} - {match['confidence']}% | Powody: {reasons_str}")

    # JeĹ›li nie ma dopasowaĹ„, zaloguj to
    if not matches:
        logger.warning(f"âš ď¸Ź BRAK DOPASOWAĹ! Parametry: W={width}, H={height}, DPR={dpr}, RAM={ram}, Hz={refresh_rate}, GPU={gpu[:30]}")

    return matches[:3]

app = Flask(__name__, template_folder='templates')
CORS(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)



def validate_json(*required_fields):
    """Decorator to validate JSON request data"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400
            try:
                data = request.json
            except Exception:
                return jsonify({"error": "Invalid JSON format"}), 400
            if data is None:
                return jsonify({"error": "Request body cannot be empty"}), 400
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
            return f(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/')
def index():
    """Serve main HTML page."""
    return render_template('index.html')

@app.route('/version')
def version():
    """Endpoint diagnostyczny - sprawdź wersję kodu."""
    import sys
    has_find_top_3 = 'find_top_3_matches' in dir(sys.modules[__name__])
    return jsonify({
        "version": "v18.18",
        "python": sys.version,
        "has_find_top_3_matches": has_find_top_3,
        "mongodb": USE_MONGODB,
        "collections_initialized": detection_logs_collection is not None if USE_MONGODB else False
    })

@app.route('/api/check_brain', methods=['POST'])
@limiter.limit("30 per minute")
@validate_json('w', 'h', 'hz', 'gpu', 'canvasHash', 'dpr', 'ram', 'cores')
def check_brain():
    """Check device fingerprint against brain database."""
    try:
        d = request.json
        width = d.get('w')
        height = d.get('h')
        refresh_rate = d.get('hz')
        gpu = d.get('gpu')
        canvas_hash = d.get('canvasHash')
        dpr = d.get('dpr', 1)
        ram = d.get('ram', -1)
        cores = d.get('cores', -1)

        if not isinstance(width, (int, float)) or width <= 0 or width > 10000:
            return jsonify({"error": "Invalid width value"}), 400
        if not isinstance(height, (int, float)) or height <= 0 or height > 10000:
            return jsonify({"error": "Invalid height value"}), 400
        if not isinstance(refresh_rate, (int, float)) or refresh_rate <= 0 or refresh_rate > 1000:
            return jsonify({"error": "Invalid refresh rate value"}), 400
        if not isinstance(gpu, str) or len(gpu) > 200:
            return jsonify({"error": "Invalid GPU value"}), 400
        if not isinstance(canvas_hash, str) or len(canvas_hash) > 100:
            return jsonify({"error": "Invalid canvasHash value"}), 400
        if not isinstance(dpr, (int, float)) or dpr <= 0 or dpr > 10:
            return jsonify({"error": "Invalid DPR value"}), 400
        if not isinstance(ram, (int, float)) or ram < -1 or ram > 100:
            return jsonify({"error": "Invalid RAM value"}), 400
        if not isinstance(cores, (int, float)) or cores < -1 or cores > 100:
            return jsonify({"error": "Invalid cores value"}), 400

        user_agent = d.get('userAgent', '')

        # TYMCZASOWE LOGOWANIE - do debugowania Motoroli
        logger.info(f"đź”Ť FULL USER-AGENT: {user_agent}")
        logger.info(f"đź“Š PARAMS: W={width}, H={height}, DPR={dpr}, RAM={ram}, Hz={refresh_rate}, GPU={gpu[:50]}")

        ua_id = parse_device_from_ua(user_agent)

        logger.info(f"đź”Ť PARSED UA_ID: {ua_id}")

        detection_log = {
            "ua_detected": ua_id,
            "ua_full": user_agent[:100] + "..." if len(user_agent) > 100 else user_agent,
            "fingerprint": f"{width}x{height} @ {dpr}x DPR, {refresh_rate}Hz, RAM: {ram}GB, Cores: {cores}, GPU: {gpu}",
            "canvas_hash": canvas_hash,
            "dpr": dpr,
            "ram": ram,
            "cores": cores
        }

        # Priorytet 1: User-Agent z dokĹ‚adnym dopasowaniem w EXTERNAL_DB
        if ua_id:
            model_name = EXTERNAL_DB.get(ua_id) or STATIC_IDENTIFIERS.get(ua_id) or ANDROID_IDENTIFIERS.get(ua_id)
            if model_name:
                logger.info(f"âś… Device identified via UA_EXACT: {model_name}")
                accessory_codes = ACCESSORY_CODES.get(model_name, {"screen": "N/A", "case": "N/A"})
                detection_log["method"] = "UA_EXACT"
                detection_log["matched_id"] = ua_id

                # Zapisz log sukcesu
                if USE_MONGODB and detection_logs_collection is not None:
                    try:
                        detection_logs_collection.insert_one({
                            "timestamp": datetime.utcnow(),
                            "status": "SUCCESS_UA",
                            "model": model_name,
                            "confidence": 100,
                            "method": "UA_EXACT",
                            "ua_id": ua_id,
                            "fingerprint": f"{width}x{height} @ {dpr}x DPR, {refresh_rate}Hz, RAM: {ram}GB",
                            "gpu": gpu,
                            "user_agent": user_agent[:200]
                        })
                    except Exception as e:
                        logger.error(f"Error saving detection log: {e}")

                return jsonify({
                    "found": True,
                    "model": model_name,
                    "confidence": 100,
                    "source": "UA_EXACT",
                    "codes": accessory_codes,
                    "detection_log": detection_log
                })

            # Priorytet 2: User-Agent wykryty, ale nie ma w bazie - zwrĂłÄ‡ surowy ID
            logger.info(f"âś… Device identified via UA_RAW: {ua_id}")
            detection_log["method"] = "UA_RAW"
            detection_log["matched_id"] = ua_id

            # Zapisz log sukcesu
            if USE_MONGODB and detection_logs_collection is not None:
                try:
                    detection_logs_collection.insert_one({
                        "timestamp": datetime.utcnow(),
                        "status": "SUCCESS_UA_RAW",
                        "model": ua_id,
                        "confidence": 90,
                        "method": "UA_CODE",
                        "ua_id": ua_id,
                        "fingerprint": f"{width}x{height} @ {dpr}x DPR, {refresh_rate}Hz, RAM: {ram}GB",
                        "gpu": gpu,
                        "user_agent": user_agent[:200]
                    })
                except Exception as e:
                    logger.error(f"Error saving detection log: {e}")

            return jsonify({
                "found": True,
                "model": ua_id,
                "confidence": 90,
                "source": "UA_CODE",
                "codes": {"screen": "N/A", "case": "N/A"},
                "detection_log": detection_log
            })

        # Priorytet 3: Baza AI (fingerprint) - NOWA SYGNATURA Z DPR I RAM
        # ZaokrÄ…glij DPR do 2 miejsc po przecinku (3.0000001192092896 â†’ 3.0)
        dpr_rounded = round(float(dpr), 2)
        signature = f"{width}_{height}_{dpr_rounded}_{ram}_{refresh_rate}_{gpu}_{canvas_hash}"

        if signature in BRAIN:
            models = BRAIN[signature]
            top_model = max(models, key=models.get)
            total_count = sum(models.values())
            confidence = int((models[top_model] / total_count) * 100)
            logger.info(f"âś… Device identified via AI: {top_model} ({confidence}% confidence)")
            accessory_codes = ACCESSORY_CODES.get(top_model, {"screen": "N/A", "case": "N/A"})
            detection_log["method"] = "AI_FINGERPRINT"
            detection_log["signature"] = signature
            detection_log["ai_models"] = dict(models)

            # Zapisz log sukcesu
            if USE_MONGODB and detection_logs_collection is not None:
                try:
                    detection_logs_collection.insert_one({
                        "timestamp": datetime.utcnow(),
                        "status": "SUCCESS_AI",
                        "model": top_model,
                        "confidence": confidence,
                        "method": "AI_FINGERPRINT",
                        "fingerprint": f"{width}x{height} @ {dpr}x DPR, {refresh_rate}Hz, RAM: {ram}GB",
                        "gpu": gpu,
                        "user_agent": user_agent[:200],
                        "ai_models": dict(models)
                    })
                except Exception as e:
                    logger.error(f"Error saving detection log: {e}")

            return jsonify({
                "found": True,
                "model": top_model,
                "confidence": confidence,
                "source": "AI",
                "codes": accessory_codes,
                "detection_log": detection_log
            })

        # Priorytet 4: Heurystyka - znajdĹş 3 najlepiej dopasowane modele z caĹ‚ej bazy
        suggestions = find_top_3_matches(width, height, refresh_rate, gpu, dpr, ram, cores)

        if suggestions:
            detection_log["method"] = "HEURISTIC_TOP3"
            detection_log["suggestions"] = suggestions

            # AUTOMATYCZNA DECYZJA: JeĹ›li pierwszy model ma â‰Ą90% a drugi <60%, uznaj automatycznie
            if len(suggestions) >= 1:
                top_confidence = suggestions[0]["confidence"]
                second_confidence = suggestions[1]["confidence"] if len(suggestions) >= 2 else 0

                if top_confidence >= 90 and second_confidence < 60:
                    # Automatyczna decyzja - pewnoĹ›Ä‡ wystarczajÄ…co wysoka
                    model_name = suggestions[0]["model"]
                    # UsuĹ„ "(symulacja?)" z nazwy przy szukaniu kodĂłw akcesoriĂłw
                    clean_model_name = model_name.replace(" (symulacja?)", "")
                    accessory_codes = ACCESSORY_CODES.get(clean_model_name, {"screen": "N/A", "case": "N/A"})

                    logger.info(f"âś… AUTO-DECISION: {model_name} ({top_confidence}% vs {second_confidence}%)")

                    # Zapisz log sukcesu
                    if USE_MONGODB and detection_logs_collection is not None:
                        try:
                            detection_logs_collection.insert_one({
                                "timestamp": datetime.utcnow(),
                                "status": "SUCCESS_AUTO",
                                "model": model_name,
                                "confidence": top_confidence,
                                "method": "HEURISTIC_AUTO",
                                "fingerprint": f"{width}x{height} @ {dpr}x DPR, {refresh_rate}Hz, RAM: {ram}GB",
                                "gpu": gpu,
                                "user_agent": user_agent[:200]
                            })
                        except Exception as e:
                            logger.error(f"Error saving detection log: {e}")

                    return jsonify({
                        "found": True,
                        "model": model_name,
                        "confidence": top_confidence,
                        "source": "HEURISTIC_AUTO",
                        "codes": accessory_codes,
                        "detection_log": detection_log,
                        "auto_decision": True
                    })

            # Brak automatycznej decyzji - pokaĹĽ sugestie
            logger.info(f"Device not found - suggesting top 3 matches")

            # Zapisz log poraĹĽki
            if USE_MONGODB and detection_logs_collection is not None:
                try:
                    detection_logs_collection.insert_one({
                        "timestamp": datetime.utcnow(),
                        "status": "FAILED",
                        "suggestions": [s["model"] for s in suggestions[:3]],
                        "top_confidence": suggestions[0]["confidence"] if suggestions else 0,
                        "method": "HEURISTIC_SUGGESTIONS",
                        "fingerprint": f"{width}x{height} @ {dpr}x DPR, {refresh_rate}Hz, RAM: {ram}GB",
                        "gpu": gpu,
                        "user_agent": user_agent[:200]
                    })
                except Exception as e:
                    logger.error(f"Error saving detection log: {e}")

            return jsonify({
                "found": False,
                "suggestions": suggestions,
                "codes": {"screen": "N/A", "case": "N/A"},
                "detection_log": detection_log
            })

        logger.info("Device not found in brain")
        detection_log["method"] = "NOT_FOUND"

        # Zapisz log poraĹĽki (brak sugestii)
        if USE_MONGODB and detection_logs_collection is not None:
            try:
                detection_logs_collection.insert_one({
                    "timestamp": datetime.utcnow(),
                    "status": "FAILED_NO_MATCH",
                    "method": "NOT_FOUND",
                    "fingerprint": f"{width}x{height} @ {dpr}x DPR, {refresh_rate}Hz, RAM: {ram}GB",
                    "gpu": gpu,
                    "user_agent": user_agent[:200]
                })
            except Exception as e:
                logger.error(f"Error saving detection log: {e}")

        return jsonify({
            "found": False,
            "codes": {"screen": "N/A", "case": "N/A"},
            "detection_log": detection_log
        })

    except Exception as e:
        logger.error(f"Error in check_brain: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/learn', methods=['POST'])
@limiter.limit("10 per minute")
@validate_json('w', 'h', 'hz', 'gpu', 'canvasHash', 'model', 'dpr', 'ram', 'cores')
def learn():
    """Teach the AI brain with new device fingerprint."""
    try:
        d = request.json
        width = d.get('w')
        height = d.get('h')
        refresh_rate = d.get('hz')
        gpu = d.get('gpu')
        canvas_hash = d.get('canvasHash')
        model = d.get('model')
        dpr = d.get('dpr', 1)
        ram = d.get('ram', -1)
        cores = d.get('cores', -1)

        if not isinstance(width, (int, float)) or width <= 0 or width > 10000:
            return jsonify({"error": "Invalid width value"}), 400
        if not isinstance(height, (int, float)) or height <= 0 or height > 10000:
            return jsonify({"error": "Invalid height value"}), 400
        if not isinstance(refresh_rate, (int, float)) or refresh_rate <= 0 or refresh_rate > 1000:
            return jsonify({"error": "Invalid refresh rate value"}), 400
        if not isinstance(gpu, str) or len(gpu) > 200:
            return jsonify({"error": "Invalid GPU value"}), 400
        if not isinstance(canvas_hash, str) or len(canvas_hash) > 100:
            return jsonify({"error": "Invalid canvasHash value"}), 400
        if not isinstance(model, str) or len(model) > 100 or len(model) == 0:
            return jsonify({"error": "Invalid model value"}), 400
        if not isinstance(dpr, (int, float)) or dpr <= 0 or dpr > 10:
            return jsonify({"error": "Invalid DPR value"}), 400
        if not isinstance(ram, (int, float)) or ram < -1 or ram > 100:
            return jsonify({"error": "Invalid RAM value"}), 400
        if not isinstance(cores, (int, float)) or cores < -1 or cores > 100:
            return jsonify({"error": "Invalid cores value"}), 400

        # ZaokrÄ…glij DPR do 2 miejsc po przecinku (musi byÄ‡ identyczne jak w check_brain!)
        dpr_rounded = round(float(dpr), 2)
        signature = f"{width}_{height}_{dpr_rounded}_{ram}_{refresh_rate}_{gpu}_{canvas_hash}"

        if signature not in BRAIN and len(BRAIN) >= MAX_BRAIN_SIGNATURES:
            oldest_signature = next(iter(BRAIN))
            del BRAIN[oldest_signature]
            logger.warning(f"Brain limit reached. Removed oldest signature")

        if signature not in BRAIN:
            BRAIN[signature] = {}

        if (model not in BRAIN[signature] and
                len(BRAIN[signature]) >= MAX_MODELS_PER_SIGNATURE):
            min_model = min(BRAIN[signature], key=BRAIN[signature].get)
            del BRAIN[signature][min_model]
            logger.warning(f"Model limit reached for signature. Removed: {min_model}")

        if model not in BRAIN[signature]:
            BRAIN[signature][model] = 0

        BRAIN[signature][model] += 1

        save_brain()

        logger.info(f"AI learned: {model}")
        return jsonify({
            "status": "OK",
            "message": "Model learned successfully"
        })

    except Exception as e:
        logger.error(f"Error in learn: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# PANEL ADMINISTRACYJNY - ZarzÄ…dzanie BazÄ… Danych
# ============================================================================

@app.route('/admin')
def admin_panel():
    """Panel administracyjny do zarzÄ…dzania bazÄ… AI Brain i kodami akcesoriĂłw."""
    return render_template('admin.html')

@app.route('/admin/api/brain')
def admin_get_brain():
    """API: Pobierz dane z bazy AI Brain."""
    try:
        unique_models = set()
        for models in BRAIN.values():
            unique_models.update(models.keys())

        return jsonify({
            "brain_count": len(BRAIN),
            "unique_models": len(unique_models),
            "external_db_count": len(EXTERNAL_DB),
            "total_models": len(unique_models) + len(EXTERNAL_DB),
            "storage_type": "MongoDB" if USE_MONGODB else "JSON",
            "brain_data": BRAIN
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/api/brain/clear', methods=['POST'])
def admin_clear_brain():
    """API: WyczyĹ›Ä‡ caĹ‚Ä… bazÄ™ AI Brain."""
    try:
        global BRAIN
        BRAIN = {}
        save_brain()
        logger.warning("âš ď¸Ź ADMIN: Brain database cleared!")
        return jsonify({"status": "OK", "message": "âś… Baza AI wyczyszczona!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/api/models/import-matomo', methods=['POST'])
def admin_import_matomo_models():
    """API: Importuj modele z Matomo Device Detector do EXTERNAL_DB."""
    try:
        import requests
        import yaml

        MATOMO_URL = "https://raw.githubusercontent.com/matomo-org/device-detector/master/regexes/device/mobiles.yml"

        logger.info("đź“Ą Pobieranie danych z Matomo...")
        response = requests.get(MATOMO_URL, timeout=30)
        response.raise_for_status()
        devices_data = yaml.safe_load(response.text)

        global EXTERNAL_DB
        new_models = 0
        updated_models = 0

        # Matomo YAML ma strukturÄ™: {brand_name: {models: [...], device: ..., regex: ...}}
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

                device_id = regex.replace('[', '').replace(']', '').replace('?', '')
                device_id = device_id.replace('(', '').replace(')', '').replace('|', '')
                device_id = device_id.replace('\\', '').replace('+', '').replace('.', '')
                device_id = device_id.split()[0] if ' ' in device_id else device_id
                device_id = device_id[:20].strip()

                if not device_id or len(device_id) < 2:
                    continue

                full_name = f"{brand} {model_name}" if brand.lower() not in model_name.lower() else model_name

                # Unikaj duplikatĂłw - jeĹ›li klucz juĹĽ istnieje, dodaj suffix
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

        # KLUCZOWE: Zapisz do MongoDB (trwaĹ‚e na Render)
        if USE_MONGODB and external_db_collection is not None:
            try:
                external_db_collection.update_one(
                    {'_id': 'external_db'},
                    {'$set': {'data': EXTERNAL_DB, 'updated_at': datetime.utcnow()}},
                    upsert=True
                )
                logger.info(f"âś… Saved {len(EXTERNAL_DB)} models to MongoDB!")
            except Exception as e:
                logger.error(f"âťŚ Failed to save models to MongoDB: {e}")

        # Zapisz do pliku JSON (backup lokalny - ulotny na Render)
        external_db_file = 'shark_external_db.json'
        with open(external_db_file, 'w', encoding='utf-8') as f:
            json.dump(EXTERNAL_DB, f, indent=2, ensure_ascii=False)

        logger.warning(f"âš ď¸Ź ADMIN: Matomo imported! New: {new_models}, Updated: {updated_models}")
        logger.info(f"đź’ľ Saved to MongoDB and {external_db_file}")

        return jsonify({
            "status": "OK",
            "message": f"âś… Zaimportowano modele z Matomo!",
            "new_models": new_models,
            "updated_models": updated_models,
            "total_models": len(EXTERNAL_DB)
        })

    except Exception as e:
        logger.error(f"âťŚ BĹ‚Ä…d importu Matomo: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/api/models/export')
def admin_export_models():
    """API: Eksportuj bazÄ™ EXTERNAL_DB do JSON."""
    try:
        return jsonify({
            "status": "OK",
            "models_count": len(EXTERNAL_DB),
            "models_data": EXTERNAL_DB
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/api/verified-models', methods=['GET'])
def admin_get_verified_models():
    """API: Pobierz wszystkie zweryfikowane modele."""
    try:
        if USE_MONGODB and verified_models_collection is not None:
            models = list(verified_models_collection.find({}, {'_id': 0}))
            return jsonify({"status": "OK", "models": models, "count": len(models)})
        else:
            return jsonify({"status": "ERROR", "error": "MongoDB not available"}), 500
    except Exception as e:
        logger.error(f"Error getting verified models: {e}")
        return jsonify({"status": "ERROR", "error": str(e)}), 500

@app.route('/admin/api/verified-models', methods=['POST'])
def admin_add_verified_model():
    """API: Dodaj nowy zweryfikowany model."""
    try:
        data = request.json
        required_fields = ['name', 'system_name', 'w', 'h', 'dpr', 'ram', 'hz', 'gpu']

        for field in required_fields:
            if field not in data:
                return jsonify({"status": "ERROR", "error": f"Missing field: {field}"}), 400

        if USE_MONGODB and verified_models_collection is not None:
            # SprawdĹş czy model juĹĽ istnieje
            existing = verified_models_collection.find_one({'system_name': data['system_name']})
            if existing:
                return jsonify({"status": "ERROR", "error": "Model already exists"}), 400

            verified_models_collection.insert_one(data)
            logger.info(f"Added verified model: {data['system_name']}")
            return jsonify({"status": "OK", "message": "Model added successfully"})
        else:
            return jsonify({"status": "ERROR", "error": "MongoDB not available"}), 500
    except Exception as e:
        logger.error(f"Error adding verified model: {e}")
        return jsonify({"status": "ERROR", "error": str(e)}), 500

@app.route('/admin/api/verified-models/<system_name>', methods=['PUT'])
def admin_update_verified_model(system_name):
    """API: Aktualizuj zweryfikowany model."""
    try:
        data = request.json

        if USE_MONGODB and verified_models_collection is not None:
            result = verified_models_collection.update_one(
                {'system_name': system_name},
                {'$set': data}
            )

            if result.modified_count > 0:
                logger.info(f"Updated verified model: {system_name}")
                return jsonify({"status": "OK", "message": "Model updated successfully"})
            else:
                return jsonify({"status": "ERROR", "error": "Model not found"}), 404
        else:
            return jsonify({"status": "ERROR", "error": "MongoDB not available"}), 500
    except Exception as e:
        logger.error(f"Error updating verified model: {e}")
        return jsonify({"status": "ERROR", "error": str(e)}), 500

@app.route('/admin/api/verified-models/<system_name>', methods=['DELETE'])
def admin_delete_verified_model(system_name):
    """API: UsuĹ„ zweryfikowany model."""
    try:
        if USE_MONGODB and verified_models_collection is not None:
            result = verified_models_collection.delete_one({'system_name': system_name})

            if result.deleted_count > 0:
                logger.info(f"Deleted verified model: {system_name}")
                return jsonify({"status": "OK", "message": "Model deleted successfully"})
            else:
                return jsonify({"status": "ERROR", "error": "Model not found"}), 404
        else:
            return jsonify({"status": "ERROR", "error": "MongoDB not available"}), 500
    except Exception as e:
        logger.error(f"Error deleting verified model: {e}")
        return jsonify({"status": "ERROR", "error": str(e)}), 500

@app.route('/admin/api/detection-logs', methods=['GET'])
def admin_get_detection_logs():
    """API: Pobierz logi rozpoznaĹ„ (sukces i poraĹĽka)."""
    try:
        if USE_MONGODB and detection_logs_collection is not None:
            # Pobierz ostatnie 100 logĂłw
            logs = list(detection_logs_collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(100))

            # Statystyki
            total_logs = detection_logs_collection.count_documents({})
            success_count = detection_logs_collection.count_documents({'status': {'$regex': '^SUCCESS'}})
            failed_count = detection_logs_collection.count_documents({'status': {'$regex': '^FAILED'}})

            return jsonify({
                "status": "OK",
                "logs": logs,
                "stats": {
                    "total": total_logs,
                    "success": success_count,
                    "failed": failed_count,
                    "success_rate": round((success_count / total_logs * 100) if total_logs > 0 else 0, 1)
                }
            })
        else:
            return jsonify({"status": "ERROR", "error": "MongoDB not available"}), 500
    except Exception as e:
        logger.error(f"Error getting detection logs: {e}")
        return jsonify({"status": "ERROR", "error": str(e)}), 500

@app.route('/admin/api/detection-logs/clear', methods=['POST'])
def admin_clear_detection_logs():
    """API: WyczyĹ›Ä‡ logi rozpoznaĹ„."""
    try:
        if USE_MONGODB and detection_logs_collection is not None:
            result = detection_logs_collection.delete_many({})
            logger.warning(f"âš ď¸Ź ADMIN: Detection logs cleared! Deleted {result.deleted_count} logs")
            return jsonify({"status": "OK", "message": f"âś… UsuniÄ™to {result.deleted_count} logĂłw!"})
        else:
            return jsonify({"status": "ERROR", "error": "MongoDB not available"}), 500
    except Exception as e:
        logger.error(f"Error clearing detection logs: {e}")
        return jsonify({"status": "ERROR", "error": str(e)}), 500

@app.route('/admin/api/sync-to-mongodb', methods=['POST'])
def admin_sync_to_mongodb():
    """API: Synchronizuj wszystkie dane do MongoDB."""
    try:
        if not USE_MONGODB:
            error_msg = "MongoDB nie jest dostÄ™pne. Ustaw zmienne Ĺ›rodowiskowe MONGODB_URI i MONGODB_DB."
            return jsonify({
                "status": "ERROR",
                "error": error_msg,
                "help": "Lokalnie: ustaw zmienne w pliku .env lub systemowo. Na Render: zmienne sÄ… juĹĽ ustawione."
            }), 500

        results = {}

        # 1. Synchronizuj STATIC_IDENTIFIERS
        try:
            static_identifiers_collection.update_one(
                {'_id': 'static_identifiers'},
                {'$set': {'data': STATIC_IDENTIFIERS, 'updated_at': datetime.utcnow()}},
                upsert=True
            )
            results['static_identifiers'] = len(STATIC_IDENTIFIERS)
            logger.info(f"âś… Static Identifiers synced: {len(STATIC_IDENTIFIERS)} models")
        except Exception as e:
            results['static_identifiers'] = f"ERROR: {e}"

        # 2. Synchronizuj ANDROID_IDENTIFIERS
        try:
            android_identifiers_collection.update_one(
                {'_id': 'android_identifiers'},
                {'$set': {'data': ANDROID_IDENTIFIERS, 'updated_at': datetime.utcnow()}},
                upsert=True
            )
            results['android_identifiers'] = len(ANDROID_IDENTIFIERS)
            logger.info(f"âś… Android Identifiers synced: {len(ANDROID_IDENTIFIERS)} models")
        except Exception as e:
            results['android_identifiers'] = f"ERROR: {e}"

        # 3. Synchronizuj ACCESSORY_CODES
        try:
            accessory_codes_collection.update_one(
                {'_id': 'accessory_codes'},
                {'$set': {'data': ACCESSORY_CODES, 'updated_at': datetime.utcnow()}},
                upsert=True
            )
            results['accessory_codes'] = len(ACCESSORY_CODES)
            logger.info(f"âś… Accessory Codes synced: {len(ACCESSORY_CODES)} models")
        except Exception as e:
            results['accessory_codes'] = f"ERROR: {e}"

        # 4. Synchronizuj EXTERNAL_DB (Matomo)
        try:
            external_db_collection.update_one(
                {'_id': 'external_db'},
                {'$set': {'data': EXTERNAL_DB, 'updated_at': datetime.utcnow()}},
                upsert=True
            )
            results['external_db'] = len(EXTERNAL_DB)
            logger.info(f"âś… External DB synced: {len(EXTERNAL_DB)} models")
        except Exception as e:
            results['external_db'] = f"ERROR: {e}"

        # 5. Synchronizuj BRAIN (juĹĽ istnieje, ale dla pewnoĹ›ci)
        try:
            brain_collection.update_one(
                {'_id': 'brain_v18'},
                {'$set': {'data': BRAIN, 'updated_at': datetime.utcnow()}},
                upsert=True
            )
            results['brain'] = len(BRAIN)
            logger.info(f"âś… Brain synced: {len(BRAIN)} signatures")
        except Exception as e:
            results['brain'] = f"ERROR: {e}"

        logger.warning(f"đź”„ ADMIN: All data synced to MongoDB!")
        return jsonify({
            "status": "OK",
            "message": "âś… Wszystkie dane zsynchronizowane do MongoDB!",
            "results": results
        })

    except Exception as e:
        logger.error(f"Error syncing to MongoDB: {e}")
        return jsonify({"status": "ERROR", "error": str(e)}), 500

load_data()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))

    print(f"\n{'='*60}")
    print(f"SHARK v18 CLOUD | Port: {port}")
    print(f"Brain signatures: {len(BRAIN)}")
    print(f"Storage: {'MongoDB âś…' if USE_MONGODB else 'JSON File đź“'}")
    print(f"Max signatures: {MAX_BRAIN_SIGNATURES}")
    print(f"{'='*60}\n")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )
