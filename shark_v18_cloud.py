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

# MongoDB (opcjonalnie)
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("⚠️ PyMongo not installed. Using JSON file storage.")

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

# --- MONGODB SETUP (jeśli dostępne) ---
MONGODB_URI = os.environ.get('MONGODB_URI', None)
MONGODB_DB = os.environ.get('MONGODB_DB', 'shark_db')
USE_MONGODB = MONGODB_AVAILABLE and MONGODB_URI

if USE_MONGODB:
    try:
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command('ping')
        db = mongo_client[MONGODB_DB]
        brain_collection = db['brain']
        logs_collection = db['logs']
        logger.info("✅ MongoDB connected successfully")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        USE_MONGODB = False
        db = None
else:
    db = None
    logger.info("📁 Using JSON file storage (no MongoDB)")

# --- IDENTYFIKATORY URZĄDZEŃ ---
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

def load_data():
    """Load brain data from MongoDB or JSON file."""
    global BRAIN, EXTERNAL_DB
    try:
        if USE_MONGODB:
            brain_data = brain_collection.find_one({'_id': 'brain_v18'})
            if brain_data:
                BRAIN = brain_data.get('data', {})
                logger.info(f"Brain loaded from MongoDB: {len(BRAIN)} signatures")
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

    # Załaduj bazę modeli z pliku JSON (jeśli istnieje) lub użyj domyślnych
    EXTERNAL_DB = {**STATIC_IDENTIFIERS, **ANDROID_IDENTIFIERS}

    external_db_file = 'shark_external_db.json'
    if os.path.exists(external_db_file):
        try:
            with open(external_db_file, 'r', encoding='utf-8') as f:
                loaded_db = json.load(f)
                EXTERNAL_DB.update(loaded_db)
                logger.info(f"✅ External DB loaded: {len(EXTERNAL_DB)} models")
        except Exception as e:
            logger.error(f"Error loading external DB: {e}")
    else:
        logger.warning(f"⚠️ External DB file not found. Using default models only ({len(EXTERNAL_DB)} models)")
        logger.info("💡 Run 'python setup_database.py' to import 1000+ models from Matomo")

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
            # Próbuj wyciągnąć nazwę modelu
            match_moto_name = re.search(r'(moto [a-z0-9 ]+|edge [a-z0-9 ]+|razr [a-z0-9 ]+)', ua.lower())
            if match_moto_name:
                return match_moto_name.group(1).strip()
    except Exception as e:
        logger.error(f"Error parsing UA: {e}")
    return None

def find_top_3_matches(width, height, refresh_rate, gpu):
    """Find top 3 best matching models from EXTERNAL_DB based on heuristics."""
    # Baza heurystyczna z typowymi parametrami urządzeń
    HEURISTIC_DB = {
        # iPhone
        "iPhone 17 Pro Max": {"w": 440, "h": 956, "hz": 120, "gpu": "a19"},
        "iPhone 17 Pro": {"w": 402, "h": 874, "hz": 120, "gpu": "a19"},
        "iPhone 16 Pro Max": {"w": 440, "h": 956, "hz": 120, "gpu": "a18"},
        "iPhone 16 Pro": {"w": 402, "h": 874, "hz": 120, "gpu": "a18"},
        "iPhone 16": {"w": 393, "h": 852, "hz": 60, "gpu": "a18"},
        "iPhone 16 Plus": {"w": 430, "h": 932, "hz": 60, "gpu": "a18"},
        "iPhone 15 Pro Max": {"w": 430, "h": 932, "hz": 120, "gpu": "a17"},
        "iPhone 15 Pro": {"w": 393, "h": 852, "hz": 120, "gpu": "a17"},
        "iPhone 15": {"w": 393, "h": 852, "hz": 60, "gpu": "a16"},
        "iPhone 15 Plus": {"w": 430, "h": 932, "hz": 60, "gpu": "a16"},
        "iPhone 14 Pro Max": {"w": 430, "h": 932, "hz": 120, "gpu": "a16"},
        "iPhone 14 Pro": {"w": 393, "h": 852, "hz": 120, "gpu": "a16"},
        "iPhone 14": {"w": 390, "h": 844, "hz": 60, "gpu": "a15"},
        "iPhone 13 Pro Max": {"w": 428, "h": 926, "hz": 120, "gpu": "a15"},
        "iPhone 13": {"w": 390, "h": 844, "hz": 60, "gpu": "a15"},
        "iPhone 12": {"w": 390, "h": 844, "hz": 60, "gpu": "a14"},
        "iPhone 11": {"w": 414, "h": 896, "hz": 60, "gpu": "a13"},
        # Samsung
        "Samsung Galaxy S24 Ultra": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno"},
        "Samsung Galaxy S24+": {"w": 384, "h": 854, "hz": 120, "gpu": "adreno"},
        "Samsung Galaxy S24": {"w": 360, "h": 780, "hz": 120, "gpu": "adreno"},
        "Samsung Galaxy S23 Ultra": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno"},
        "Samsung Galaxy S23+": {"w": 384, "h": 854, "hz": 120, "gpu": "adreno"},
        "Samsung Galaxy S23": {"w": 360, "h": 780, "hz": 120, "gpu": "adreno"},
        "Samsung Galaxy S22 Ultra": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno"},
        "Samsung Galaxy S22": {"w": 360, "h": 780, "hz": 120, "gpu": "adreno"},
        "Samsung Galaxy S21 Ultra": {"w": 412, "h": 915, "hz": 120, "gpu": "mali"},
        "Samsung Galaxy S21": {"w": 360, "h": 780, "hz": 120, "gpu": "mali"},
        "Samsung Galaxy A54": {"w": 412, "h": 914, "hz": 120, "gpu": "adreno"},
        "Samsung Galaxy A53": {"w": 412, "h": 914, "hz": 120, "gpu": "adreno"},
        # Google Pixel
        "Google Pixel 8 Pro": {"w": 412, "h": 915, "hz": 120, "gpu": "mali"},
        "Google Pixel 8": {"w": 412, "h": 915, "hz": 120, "gpu": "mali"},
        "Google Pixel 7 Pro": {"w": 412, "h": 915, "hz": 120, "gpu": "mali"},
        "Google Pixel 7": {"w": 412, "h": 915, "hz": 90, "gpu": "mali"},
        "Google Pixel 6 Pro": {"w": 412, "h": 915, "hz": 120, "gpu": "mali"},
        "Google Pixel 6": {"w": 412, "h": 915, "hz": 90, "gpu": "mali"},
        # Xiaomi
        "Xiaomi 14 Pro": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno"},
        "Xiaomi 13 Pro": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno"},
        "Xiaomi 12 Pro": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno"},
        # OnePlus
        "OnePlus 12": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno"},
        "OnePlus 11": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno"},
        "OnePlus 10 Pro": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno"},
        # Motorola
        "Motorola Edge 50 Pro": {"w": 412, "h": 915, "hz": 144, "gpu": "adreno"},
        "Motorola Edge 50": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno"},
        "Motorola Edge 40 Pro": {"w": 412, "h": 915, "hz": 165, "gpu": "adreno"},
        "Motorola Edge 40": {"w": 412, "h": 915, "hz": 144, "gpu": "adreno"},
        "Motorola Edge 30 Ultra": {"w": 412, "h": 915, "hz": 144, "gpu": "adreno"},
        "Motorola Moto G84": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno"},
        "Motorola Razr 40 Ultra": {"w": 412, "h": 915, "hz": 165, "gpu": "adreno"},
    }

    matches = []
    gpu_lower = gpu.lower()

    for model_name, specs in HEURISTIC_DB.items():
        score = 0
        reasons = []

        # Dopasowanie rozdzielczości (50 punktów)
        if abs(specs["w"] - width) <= 2 and abs(specs["h"] - height) <= 2:
            score += 50
            reasons.append(f"Rozdzielczość: {specs['w']}x{specs['h']}")
        elif abs(specs["w"] - width) <= 10 and abs(specs["h"] - height) <= 10:
            score += 30
            reasons.append(f"Rozdzielczość ~{specs['w']}x{specs['h']}")

        # Dopasowanie odświeżania (30 punktów)
        if specs["hz"] == refresh_rate:
            score += 30
            reasons.append(f"Odświeżanie: {specs['hz']}Hz")

        # Dopasowanie GPU (20 punktów)
        if specs["gpu"] in gpu_lower or gpu_lower in specs["gpu"]:
            score += 20
            reasons.append(f"GPU: {specs['gpu']}")

        if score > 0:
            matches.append({
                "model": model_name,
                "confidence": min(score, 100),
                "reasons": reasons
            })

    # Sortuj po confidence i zwróć top 3
    matches.sort(key=lambda x: x["confidence"], reverse=True)
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

@app.route('/api/check_brain', methods=['POST'])
@limiter.limit("30 per minute")
@validate_json('w', 'h', 'hz', 'gpu', 'canvasHash')
def check_brain():
    """Check device fingerprint against brain database."""
    try:
        d = request.json
        width = d.get('w')
        height = d.get('h')
        refresh_rate = d.get('hz')
        gpu = d.get('gpu')
        canvas_hash = d.get('canvasHash')

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

        user_agent = d.get('userAgent', '')
        ua_id = parse_device_from_ua(user_agent)

        detection_log = {
            "ua_detected": ua_id,
            "ua_full": user_agent[:100] + "..." if len(user_agent) > 100 else user_agent,
            "fingerprint": f"{width}x{height} @ {refresh_rate}Hz, GPU: {gpu}",
            "canvas_hash": canvas_hash
        }

        # Priorytet 1: User-Agent z dokładnym dopasowaniem w EXTERNAL_DB
        if ua_id:
            model_name = EXTERNAL_DB.get(ua_id) or STATIC_IDENTIFIERS.get(ua_id) or ANDROID_IDENTIFIERS.get(ua_id)
            if model_name:
                logger.info(f"Device identified via UA_EXACT: {model_name}")
                accessory_codes = ACCESSORY_CODES.get(model_name, {"screen": "N/A", "case": "N/A"})
                detection_log["method"] = "UA_EXACT"
                detection_log["matched_id"] = ua_id
                return jsonify({
                    "found": True,
                    "model": model_name,
                    "confidence": 100,
                    "source": "UA_EXACT",
                    "codes": accessory_codes,
                    "detection_log": detection_log
                })

            # Priorytet 2: User-Agent wykryty, ale nie ma w bazie - zwróć surowy ID
            logger.info(f"Device identified via UA_RAW: {ua_id}")
            detection_log["method"] = "UA_RAW"
            detection_log["matched_id"] = ua_id
            return jsonify({
                "found": True,
                "model": ua_id,
                "confidence": 90,
                "source": "UA_CODE",
                "codes": {"screen": "N/A", "case": "N/A"},
                "detection_log": detection_log
            })

        # Priorytet 3: Baza AI (fingerprint)
        signature = f"{width}_{height}_{refresh_rate}_{gpu}_{canvas_hash}"

        if signature in BRAIN:
            models = BRAIN[signature]
            top_model = max(models, key=models.get)
            total_count = sum(models.values())
            confidence = int((models[top_model] / total_count) * 100)
            logger.info(f"Device identified via AI: {top_model} ({confidence}% confidence)")
            accessory_codes = ACCESSORY_CODES.get(top_model, {"screen": "N/A", "case": "N/A"})
            detection_log["method"] = "AI_FINGERPRINT"
            detection_log["signature"] = signature
            detection_log["ai_models"] = dict(models)
            return jsonify({
                "found": True,
                "model": top_model,
                "confidence": confidence,
                "source": "AI",
                "codes": accessory_codes,
                "detection_log": detection_log
            })

        # Priorytet 4: Heurystyka - znajdź 3 najlepiej dopasowane modele z całej bazy
        suggestions = find_top_3_matches(width, height, refresh_rate, gpu)

        if suggestions:
            detection_log["method"] = "HEURISTIC_TOP3"
            detection_log["suggestions"] = suggestions
            logger.info(f"Device not found - suggesting top 3 matches")
            return jsonify({
                "found": False,
                "suggestions": suggestions,
                "codes": {"screen": "N/A", "case": "N/A"},
                "detection_log": detection_log
            })

        logger.info("Device not found in brain")
        detection_log["method"] = "NOT_FOUND"
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
@validate_json('w', 'h', 'hz', 'gpu', 'canvasHash', 'model')
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

        signature = f"{width}_{height}_{refresh_rate}_{gpu}_{canvas_hash}"

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
# PANEL ADMINISTRACYJNY - Zarządzanie Bazą Danych
# ============================================================================

@app.route('/admin')
def admin_panel():
    """Panel administracyjny do zarządzania bazą AI Brain i kodami akcesoriów."""
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
    """API: Wyczyść całą bazę AI Brain."""
    try:
        global BRAIN
        BRAIN = {}
        save_brain()
        logger.warning("⚠️ ADMIN: Brain database cleared!")
        return jsonify({"status": "OK", "message": "✅ Baza AI wyczyszczona!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/api/models/import-matomo', methods=['POST'])
def admin_import_matomo_models():
    """API: Importuj modele z Matomo Device Detector do EXTERNAL_DB."""
    try:
        import requests
        import yaml

        MATOMO_URL = "https://raw.githubusercontent.com/matomo-org/device-detector/master/regexes/device/mobiles.yml"

        logger.info("📥 Pobieranie danych z Matomo...")
        response = requests.get(MATOMO_URL, timeout=30)
        response.raise_for_status()
        devices_data = yaml.safe_load(response.text)

        global EXTERNAL_DB
        new_models = 0
        updated_models = 0

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

                device_id = regex.replace('[', '').replace(']', '').replace('?', '')
                device_id = device_id.replace('(', '').replace(')', '').replace('|', '')
                device_id = device_id.replace('\\', '').replace('+', '').replace('.', '')
                device_id = device_id.split()[0] if ' ' in device_id else device_id
                device_id = device_id[:20].strip()

                if not device_id or len(device_id) < 2:
                    continue

                full_name = f"{brand} {model_name}" if brand.lower() not in model_name.lower() else model_name

                # Unikaj duplikatów - jeśli klucz już istnieje, dodaj suffix
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

        # Zapisz do pliku JSON, żeby przetrwało restart
        external_db_file = 'shark_external_db.json'
        with open(external_db_file, 'w', encoding='utf-8') as f:
            json.dump(EXTERNAL_DB, f, indent=2, ensure_ascii=False)

        logger.warning(f"⚠️ ADMIN: Matomo imported! New: {new_models}, Updated: {updated_models}")
        logger.info(f"💾 Saved to {external_db_file}")

        return jsonify({
            "status": "OK",
            "message": f"✅ Zaimportowano modele z Matomo!",
            "new_models": new_models,
            "updated_models": updated_models,
            "total_models": len(EXTERNAL_DB)
        })

    except Exception as e:
        logger.error(f"❌ Błąd importu Matomo: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/api/models/export')
def admin_export_models():
    """API: Eksportuj bazę EXTERNAL_DB do JSON."""
    try:
        return jsonify({
            "status": "OK",
            "models_count": len(EXTERNAL_DB),
            "models_data": EXTERNAL_DB
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    load_data()

    port = int(os.environ.get('PORT', 5000))

    print(f"\n{'='*60}")
    print(f"SHARK v18 CLOUD | Port: {port}")
    print(f"Brain signatures: {len(BRAIN)}")
    print(f"Storage: {'MongoDB ✅' if USE_MONGODB else 'JSON File 📁'}")
    print(f"Max signatures: {MAX_BRAIN_SIGNATURES}")
    print(f"{'='*60}\n")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )
