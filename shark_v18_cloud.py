import json
import logging
import os
import re
from collections import deque
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify
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

    EXTERNAL_DB = {**STATIC_IDENTIFIERS, **ANDROID_IDENTIFIERS}

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
    except Exception as e:
        logger.error(f"Error parsing UA: {e}")
    return None

app = Flask(__name__)
CORS(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

CLIENT_HTML = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="theme-color" content="#F2F2F7">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>SHARK v18 Cloud</title>
    <style>
        :root { --ios-bg: #F2F2F7; --ios-card: #FFF; --ios-blue: #007AFF; --ios-green: #34C759; --ios-text: #000; --ios-sub: #8E8E93; --ios-sep: #C6C6C8; }
        body { font-family: -apple-system, sans-serif; background: var(--ios-bg); margin: 0; padding: env(safe-area-inset-top) 0 20px 0; color: var(--ios-text); -webkit-font-smoothing: antialiased; }
        .header { background: rgba(242,242,247,0.85); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); padding: 10px 20px; position: sticky; top: 0; z-index: 100; border-bottom: 0.5px solid rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; }
        .header h1 { margin: 0; font-size: 22px; font-weight: 700; }
        .header .status { font-size: 11px; font-weight: 600; color: var(--ios-green); background: rgba(52, 199, 89, 0.1); padding: 4px 8px; border-radius: 12px; }
        .container { padding: 20px; max-width: 600px; margin: 0 auto; }
        .ios-group { background: var(--ios-card); border-radius: 12px; overflow: hidden; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
        .group-title { font-size: 13px; color: var(--ios-sub); text-transform: uppercase; margin: 0 0 8px 15px; font-weight: 500; }
        .row { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; border-bottom: 0.5px solid var(--ios-sep); font-size: 17px; }
        .row:last-child { border-bottom: none; }
        .row .val { color: var(--ios-sub); max-width: 60%; text-align: right; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .row .val.strong { color: var(--ios-blue); font-weight: 600; }
        .btn-scan { background: var(--ios-blue); color: white; border: none; width: 100%; padding: 16px; font-size: 17px; font-weight: 600; border-radius: 12px; cursor: pointer; transition: transform 0.1s; }
        .btn-scan:active { transform: scale(0.98); opacity: 0.9; }
        #result-hero { text-align: center; padding: 30px 20px; display: none; }
        .model-name { font-size: 32px; font-weight: 700; color: var(--ios-text); line-height: 1.2; margin-bottom: 5px; }
        .conf-badge { font-size: 13px; color: var(--ios-blue); background: #eef5ff; padding: 4px 12px; border-radius: 20px; font-weight: 600; display: inline-block; }
        .code-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 16px; margin: 20px 0; text-align: center; box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3); }
        .code-label { font-size: 12px; color: rgba(255,255,255,0.8); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
        .code-value { font-size: 48px; font-weight: 900; color: white; letter-spacing: 3px; font-family: 'Courier New', monospace; text-shadow: 0 2px 10px rgba(0,0,0,0.3); }
        .code-desc { font-size: 13px; color: rgba(255,255,255,0.9); margin-top: 8px; }
        select { width: 100%; padding: 12px; border-radius: 10px; border: none; background: #E9E9EB; font-size: 16px; margin-bottom: 10px; color: var(--ios-blue); font-weight: 600; text-align: center; }
        .btn-fix { width: 100%; padding: 12px; background: transparent; color: var(--ios-green); border: none; font-weight: 600; font-size: 16px; }
    </style>
</head>
<body>
    <div class="header"><h1>SHARK v18 ☁️</h1><div class="status">ONLINE • CLOUD</div></div>
    <div id="result-hero"><div class="model-name" id="displayModel">...</div><div class="conf-badge" id="displayConf">...</div></div>
    <div class="container">
        <div class="ios-group"><div style="padding: 15px;"><button id="scanBtn" class="btn-scan" onclick="startSharkScan()">🚀 Rozpocznij Skanowanie</button></div></div>
        <div id="codesSection" style="display:none;">
            <div class="code-box"><div class="code-label">📱 Kod Szybki</div><div class="code-value" id="codeScreen">-</div><div class="code-desc">Podaj ten kod sprzedawcy</div></div>
            <div class="group-title">Dostępne Akcesoria</div>
            <div class="ios-group"><div class="row"><span>🛡️ Szkło Ochronne</span><span class="val strong" id="codeScreenDetail">-</span></div><div class="row"><span>📦 Etui</span><span class="val strong" id="codeCase">-</span></div></div>
        </div>
        <div class="group-title">Parametry</div>
        <div class="ios-group">
            <div class="row"><span>Rozdzielczość</span><span class="val" id="val-res">-</span></div>
            <div class="row"><span>Odświeżanie</span><span class="val strong" id="val-hz">-</span></div>
            <div class="row"><span>GPU</span><span class="val" id="val-gpu">-</span></div>
            <div class="row"><span>Canvas Hash</span><span class="val" id="val-hash">-</span></div>
            <div class="row"><span>UA System</span><span class="val" id="val-ua" style="font-size:10px">-</span></div>
        </div>
        <div class="group-title" id="fixTitle" style="display:none">Korekta AI</div>
        <div class="ios-group" id="fixGroup" style="display:none; padding:15px;">
            <select id="modelSelector"></select>
            <input type="text" id="customModel" placeholder="Lub wpisz nowy model (np. Motorola Edge 50)..." style="width:100%;padding:12px;border-radius:10px;border:1px solid #E9E9EB;font-size:16px;margin:10px 0;">
            <button class="btn-fix" onclick="teachBrain()">✅ Zapisz i Naucz AI</button>
        </div>
    </div>
<script>
    const DB_HEURISTIC = [
        {name:"iPhone 17 Pro Max",w:440,h:956,hz:120,gpu:"a19"}, {name:"iPhone 17 Pro",w:402,h:874,hz:120,gpu:"a19"},
        {name:"iPhone 16 Pro Max",w:440,h:956,hz:120,gpu:"a18"}, {name:"iPhone 16 Pro",w:402,h:874,hz:120,gpu:"a18"},
        {name:"iPhone 16 / Plus",w:393,h:852,hz:60,gpu:"a18"}, {name:"iPhone 15 Pro Max",w:430,h:932,hz:120,gpu:"a17"},
        {name:"iPhone 15 Pro",w:393,h:852,hz:120,gpu:"a17"}, {name:"iPhone 15 / Plus",w:393,h:852,hz:60,gpu:"a16"},
        {name:"iPhone 14 Pro Max",w:430,h:932,hz:120,gpu:"a16"}, {name:"iPhone 14 Pro",w:393,h:852,hz:120,gpu:"a16"},
        {name:"iPhone 13 Pro Max",w:428,h:926,hz:120,gpu:"a15"}, {name:"iPhone 13 / 14",w:390,h:844,hz:60,gpu:"a15"},
        {name:"iPhone 12 / Pro",w:390,h:844,hz:60,gpu:"a14"}, {name:"iPhone 11",w:414,h:896,hz:60,gpu:"a13"},
        {name:"Samsung Galaxy S24 Ultra",w:412,h:915,hz:120,gpu:"adreno"}, {name:"Samsung Galaxy S24+",w:384,h:854,hz:120,gpu:"adreno"},
        {name:"Samsung Galaxy S24",w:360,h:780,hz:120,gpu:"adreno"}, {name:"Samsung Galaxy S23 Ultra",w:412,h:915,hz:120,gpu:"adreno"},
        {name:"Samsung Galaxy S23+",w:384,h:854,hz:120,gpu:"adreno"}, {name:"Samsung Galaxy S23",w:360,h:780,hz:120,gpu:"adreno"},
        {name:"Samsung Galaxy S22 Ultra",w:412,h:915,hz:120,gpu:"adreno"}, {name:"Samsung Galaxy S22+",w:384,h:854,hz:120,gpu:"adreno"},
        {name:"Samsung Galaxy S22",w:360,h:780,hz:120,gpu:"adreno"}, {name:"Samsung Galaxy S21 Ultra",w:412,h:915,hz:120,gpu:"mali"},
        {name:"Samsung Galaxy S21+",w:384,h:854,hz:120,gpu:"mali"}, {name:"Samsung Galaxy S21",w:360,h:780,hz:120,gpu:"mali"},
        {name:"Samsung Galaxy S20 Ultra",w:412,h:915,hz:120,gpu:"mali"}, {name:"Samsung Galaxy S20+",w:384,h:854,hz:120,gpu:"mali"},
        {name:"Samsung Galaxy S20",w:360,h:800,hz:120,gpu:"mali"},
        {name:"Samsung Galaxy A54",w:412,h:914,hz:120,gpu:"adreno"}, {name:"Samsung Galaxy A53",w:412,h:914,hz:120,gpu:"adreno"},
        {name:"Samsung Galaxy A52",w:412,h:914,hz:90,gpu:"adreno"}, {name:"Samsung Galaxy A34",w:412,h:914,hz:120,gpu:"mali"},
        {name:"Samsung Galaxy A33",w:412,h:914,hz:90,gpu:"mali"},
        {name:"Google Pixel 8 Pro",w:412,h:915,hz:120,gpu:"mali"}, {name:"Google Pixel 8",w:412,h:915,hz:120,gpu:"mali"},
        {name:"Google Pixel 7 Pro",w:412,h:915,hz:120,gpu:"mali"}, {name:"Google Pixel 7",w:412,h:915,hz:90,gpu:"mali"},
        {name:"Google Pixel 6 Pro",w:412,h:915,hz:120,gpu:"mali"}, {name:"Google Pixel 6",w:412,h:915,hz:90,gpu:"mali"},
        {name:"Google Pixel 5",w:393,h:851,hz:90,gpu:"adreno"},
        {name:"Xiaomi 14 Pro",w:412,h:915,hz:120,gpu:"adreno"}, {name:"Xiaomi 14",w:412,h:915,hz:120,gpu:"adreno"},
        {name:"Xiaomi 13 Ultra",w:412,h:915,hz:120,gpu:"adreno"}, {name:"Xiaomi 13 Pro",w:412,h:915,hz:120,gpu:"adreno"},
        {name:"Xiaomi 13",w:412,h:915,hz:120,gpu:"adreno"}, {name:"Xiaomi 12 Pro",w:412,h:915,hz:120,gpu:"adreno"},
        {name:"Xiaomi 12",w:412,h:915,hz:120,gpu:"adreno"}, {name:"Xiaomi Mi 11",w:412,h:915,hz:120,gpu:"adreno"},
        {name:"OnePlus 12",w:412,h:915,hz:120,gpu:"adreno"}, {name:"OnePlus 11",w:412,h:915,hz:120,gpu:"adreno"},
        {name:"OnePlus 10 Pro",w:412,h:915,hz:120,gpu:"adreno"}, {name:"OnePlus 9 Pro",w:412,h:915,hz:120,gpu:"adreno"},
        {name:"OnePlus 9",w:412,h:915,hz:120,gpu:"adreno"}, {name:"OnePlus 8 Pro",w:412,h:915,hz:120,gpu:"adreno"},
        {name:"OnePlus 8",w:412,h:915,hz:90,gpu:"adreno"}
    ];
    const allModels=["iPhone 17 Pro Max","iPhone 17 Pro","iPhone 17","iPhone Air","iPhone 16 Pro Max","iPhone 16 Pro","iPhone 16","iPhone 16 Plus","iPhone 16e","iPhone 15 Pro Max","iPhone 15 Pro","iPhone 15","iPhone 15 Plus","iPhone 14 Pro Max","iPhone 14 Pro","iPhone 14","iPhone 14 Plus","iPhone 13 Pro Max","iPhone 13 Pro","iPhone 13","iPhone 12 Pro Max","iPhone 12 Pro","iPhone 12","iPhone 11 Pro Max","iPhone 11 Pro","iPhone 11","Samsung Galaxy S24 Ultra","Samsung Galaxy S24+","Samsung Galaxy S24","Samsung Galaxy S23 Ultra","Samsung Galaxy S23+","Samsung Galaxy S23","Samsung Galaxy S22 Ultra","Samsung Galaxy S22+","Samsung Galaxy S22","Samsung Galaxy S21 Ultra","Samsung Galaxy S21+","Samsung Galaxy S21","Samsung Galaxy S20 Ultra","Samsung Galaxy S20+","Samsung Galaxy S20","Samsung Galaxy A54","Samsung Galaxy A53","Samsung Galaxy A52","Samsung Galaxy A34","Samsung Galaxy A33","Samsung Galaxy Z Fold 5","Samsung Galaxy Z Fold 4","Samsung Galaxy Z Fold 3","Samsung Galaxy Z Flip 5","Samsung Galaxy Z Flip 4","Samsung Galaxy Z Flip 3","Google Pixel 8 Pro","Google Pixel 8","Google Pixel 7 Pro","Google Pixel 7","Google Pixel 6 Pro","Google Pixel 6","Google Pixel 5","Xiaomi 14 Pro","Xiaomi 14","Xiaomi 13 Ultra","Xiaomi 13 Pro","Xiaomi 13","Xiaomi 12 Pro","Xiaomi 12","Xiaomi Mi 11","Xiaomi Mi 10T Pro","OnePlus 12","OnePlus 11","OnePlus 10 Pro","OnePlus 9 Pro","OnePlus 9","OnePlus 8 Pro","OnePlus 8","Huawei P40 Pro","Huawei P40","Huawei P30 Pro","Huawei P30","Huawei P Smart 2019"];
    const sel=document.getElementById('modelSelector'); allModels.forEach(m=>{let o=document.createElement('option');o.value=m;o.text=m;sel.appendChild(o);});
    let currentScanData=null;
    function getCanvasHash(){try{const c=document.createElement('canvas');const ctx=c.getContext('2d');c.width=200;c.height=50;ctx.textBaseline="top";ctx.font="14px Arial";ctx.fillStyle="#f60";ctx.fillRect(125,1,62,20);ctx.fillStyle="#069";ctx.fillText("SHARK_v18",2,15);const b64=c.toDataURL().replace("data:image/png;base64,","");let h=0;for(let i=0;i<b64.length;i++){h=((h<<5)-h)+b64.charCodeAt(i);h|=0;}return h.toString(16);}catch(e){return "error";}}
    function measureHz(){return new Promise(r=>{let f=0,s=performance.now();function l(){f++;if(performance.now()-s>=500)r(Math.round(f*2)<70?60:120);else requestAnimationFrame(l);}requestAnimationFrame(l);});}
    async function startSharkScan(){
        const btn=document.getElementById('scanBtn');btn.disabled=true;btn.innerText="...";document.getElementById('result-hero').style.display='block';
        const gc=document.createElement('canvas'),gl=gc.getContext('webgl'),di=gl?gl.getExtension('WEBGL_debug_renderer_info'):null;
        let gpu=di?gl.getParameter(di.UNMASKED_RENDERER_WEBGL):"unknown";if(gpu.includes("Apple"))gpu=gpu.replace("Apple ","").replace(" GPU","").trim();
        const hz=await measureHz(),hash=getCanvasHash(),w=Math.min(screen.width,screen.height),h=Math.max(screen.width,screen.height);
        const data={w:w,h:h,hz:hz,gpu:gpu.toLowerCase(),canvasHash:hash,userAgent:navigator.userAgent,model:""};
        currentScanData=data;
        document.getElementById('val-res').innerText=`${w} x ${h}`;document.getElementById('val-hz').innerText=`${hz} Hz`;
        document.getElementById('val-gpu').innerText=gpu;document.getElementById('val-hash').innerText=hash;
        document.getElementById('val-ua').innerText=navigator.userAgent.substring(0,25)+"...";
        try{
            const res=await fetch('/api/check_brain',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
            const d=await res.json();
            if(d.found) {
                showResult(d.model,d.confidence,d.source.includes("AI")||d.source.includes("UA"));
                if(d.codes) showCodes(d.codes);
            }
            else runClientHeuristics(data);
        }catch(e){runClientHeuristics(data);}
        document.getElementById('fixTitle').style.display='block';document.getElementById('fixGroup').style.display='block';btn.innerText="Skanuj Ponownie";btn.disabled=false;
    }
    function runClientHeuristics(fp){
        let best={name:"Nieznany",score:0};
        DB_HEURISTIC.forEach(m=>{let s=0;if(Math.abs(m.w-fp.w)<=1&&Math.abs(m.h-fp.h)<=1)s+=50;if(m.hz===fp.hz)s+=30;if(fp.gpu.includes(m.gpu))s+=20;if(s>best.score)best={name:m.name,score:s};});
        showResult(best.name,best.score>=50?best.score:0,false);
    }
    function showResult(m,c,ai){const d=document.getElementById('displayModel'),b=document.getElementById('displayConf');d.innerText=m;b.innerText=ai?`🧠 PEWNOŚĆ: ${c}%`:`⚙️ ALGORYTM: ${c}%`;b.style.background=ai?'#eef5ff':'#f2f2f7';b.style.color=ai?'#007aff':'#8e8e93';const sel=document.getElementById('modelSelector');for(let i=0;i<sel.options.length;i++)if(sel.options[i].value===m){sel.selectedIndex=i;break;}}
    function showCodes(codes){
        if(!codes || (!codes.screen && !codes.case)) return;
        document.getElementById('codesSection').style.display='block';
        document.getElementById('codeScreen').innerText=codes.screen || 'N/A';
        document.getElementById('codeScreenDetail').innerText=codes.screen || 'N/A';
        document.getElementById('codeCase').innerText=codes.case || 'N/A';
    }
    async function teachBrain(){
        if(!currentScanData)return;
        const customModel=document.getElementById('customModel').value.trim();
        const selectedModel=document.getElementById('modelSelector').value;
        currentScanData.model=customModel || selectedModel;
        if(!currentScanData.model){alert("⚠️ Wybierz lub wpisz model!");return;}
        await fetch('/api/learn',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(currentScanData)});
        alert("✅ Nauczono! Model: "+currentScanData.model);
        showResult(currentScanData.model,100,true);
        document.getElementById('customModel').value='';
    }
</script></body></html>
"""

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
    return CLIENT_HTML

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

        if ua_id:
            model_name = EXTERNAL_DB.get(ua_id)
            if model_name:
                logger.info(f"Device identified via UA_EXACT: {model_name}")
                accessory_codes = ACCESSORY_CODES.get(model_name, {"screen": "N/A", "case": "N/A"})
                return jsonify({
                    "found": True,
                    "model": model_name,
                    "confidence": 100,
                    "source": "UA_EXACT",
                    "codes": accessory_codes
                })
            logger.info(f"Device identified via UA_RAW: {ua_id}")
            return jsonify({
                "found": True,
                "model": ua_id,
                "confidence": 95,
                "source": "UA_RAW",
                "codes": {"screen": "N/A", "case": "N/A"}
            })

        signature = f"{width}_{height}_{refresh_rate}_{gpu}_{canvas_hash}"

        if signature in BRAIN:
            models = BRAIN[signature]
            top_model = max(models, key=models.get)
            total_count = sum(models.values())
            confidence = int((models[top_model] / total_count) * 100)
            logger.info(f"Device identified via AI: {top_model} ({confidence}% confidence)")
            accessory_codes = ACCESSORY_CODES.get(top_model, {"screen": "N/A", "case": "N/A"})
            return jsonify({
                "found": True,
                "model": top_model,
                "confidence": confidence,
                "source": "AI",
                "codes": accessory_codes
            })

        logger.info("Device not found in brain")
        return jsonify({"found": False, "codes": {"screen": "N/A", "case": "N/A"}})

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
    return """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SHARK v18 - Panel Administracyjny</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .header h1 { font-size: 32px; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 14px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        .stat-card h3 { font-size: 14px; color: #666; margin-bottom: 10px; text-transform: uppercase; }
        .stat-card .value { font-size: 36px; font-weight: 700; color: #667eea; }
        .section { background: white; padding: 25px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        .section h2 { font-size: 20px; margin-bottom: 20px; color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        .btn { background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; transition: all 0.3s; }
        .btn:hover { background: #5568d3; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3); }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
        .btn-success { background: #27ae60; }
        .btn-success:hover { background: #229954; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: 600; color: #333; }
        tr:hover { background: #f8f9fa; }
        .badge { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
        .badge-primary { background: #e3f2fd; color: #1976d2; }
        input[type="text"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; margin-bottom: 10px; }
        .alert { padding: 15px; border-radius: 6px; margin-bottom: 20px; }
        .alert-info { background: #e3f2fd; color: #1976d2; border-left: 4px solid #1976d2; }
        .alert-success { background: #e8f5e9; color: #388e3c; border-left: 4px solid #388e3c; }
        .scrollable { max-height: 400px; overflow-y: auto; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦈 SHARK v18 - Panel Administracyjny</h1>
            <p>Zarządzanie bazą AI Brain i importem modeli</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <h3>📊 Sygnatur AI</h3>
                <div class="value" id="brainCount">-</div>
            </div>
            <div class="stat-card">
                <h3>📱 Modeli w Bazie</h3>
                <div class="value" id="modelCount">-</div>
            </div>
            <div class="stat-card">
                <h3>💾 Typ Bazy</h3>
                <div class="value" id="storageType" style="font-size: 20px;">-</div>
            </div>
        </div>

        <div class="section">
            <h2>🌐 Import Modeli z Matomo Device Detector</h2>
            <div class="alert alert-success">
                <strong>🚀 NOWE!</strong> Automatycznie importuj 1000+ modeli telefonów z bazy Matomo Device Detector!
            </div>
            <button class="btn btn-success" onclick="importMatomoModels()" id="matomoImportBtn">
                🌐 Importuj Modele z Matomo (1000+ modeli)
            </button>
            <button class="btn" onclick="exportModels()" style="margin-left: 10px;">📥 Eksportuj Bazę Modeli</button>

            <div id="matomoProgress" style="display: none; margin-top: 20px;">
                <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #667eea;">
                    <strong>⏳ Importowanie...</strong>
                    <p style="margin: 10px 0 0 0; color: #666;">Pobieranie danych z Matomo Device Detector. To może potrwać 10-30 sekund...</p>
                </div>
            </div>

            <div id="matomoResult" style="display: none; margin-top: 20px;"></div>
        </div>

        <div class="section">
            <h2>🧠 Baza AI Brain - Nauczonych Modeli</h2>
            <div class="alert alert-info">
                <strong>ℹ️ Info:</strong> Baza AI przechowuje fingerprint urządzeń i przypisane do nich modele.
            </div>
            <button class="btn" onclick="loadBrainData()">🔄 Odśwież Dane</button>
            <button class="btn btn-danger" onclick="clearBrain()" style="margin-left: 10px;">🗑️ Wyczyść Bazę AI</button>
            <div class="scrollable" style="margin-top: 20px;">
                <table>
                    <thead>
                        <tr>
                            <th>Sygnatura</th>
                            <th>Modele</th>
                            <th>Wystąpienia</th>
                        </tr>
                    </thead>
                    <tbody id="brainTableBody">
                        <tr><td colspan="3" style="text-align: center; color: #999;">Ładowanie...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        async function loadBrainData() {
            try {
                const res = await fetch('/admin/api/brain');
                const data = await res.json();

                document.getElementById('brainCount').innerText = data.brain_count;
                document.getElementById('modelCount').innerText = data.unique_models;
                document.getElementById('storageType').innerText = data.storage_type;

                const tbody = document.getElementById('brainTableBody');
                tbody.innerHTML = '';

                if (data.brain_count === 0) {
                    tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #999;">Brak danych</td></tr>';
                    return;
                }

                let count = 0;
                for (const [signature, models] of Object.entries(data.brain_data)) {
                    if (count >= 50) break;
                    const row = document.createElement('tr');
                    const modelsList = Object.entries(models).map(([m, c]) => `${m} (${c}x)`).join(', ');
                    const totalCount = Object.values(models).reduce((a, b) => a + b, 0);
                    row.innerHTML = `
                        <td><code style="font-size: 11px;">${signature.substring(0, 40)}...</code></td>
                        <td>${modelsList}</td>
                        <td><span class="badge badge-primary">${totalCount}</span></td>
                    `;
                    tbody.appendChild(row);
                    count++;
                }
            } catch (e) {
                alert('Błąd: ' + e.message);
            }
        }

        async function clearBrain() {
            if (!confirm('⚠️ Wyczyścić CAŁĄ bazę AI?')) return;
            try {
                const res = await fetch('/admin/api/brain/clear', { method: 'POST' });
                const data = await res.json();
                alert(data.message);
                loadBrainData();
            } catch (e) {
                alert('Błąd: ' + e.message);
            }
        }

        async function importMatomoModels() {
            if (!confirm('🌐 Importować 1000+ modeli z Matomo?\n\nTo może potrwać 10-30 sekund.')) return;

            const btn = document.getElementById('matomoImportBtn');
            const progress = document.getElementById('matomoProgress');
            const result = document.getElementById('matomoResult');

            btn.disabled = true;
            btn.innerText = '⏳ Importowanie...';
            progress.style.display = 'block';
            result.style.display = 'none';

            try {
                const res = await fetch('/admin/api/models/import-matomo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await res.json();

                progress.style.display = 'none';

                if (data.status === 'OK') {
                    result.innerHTML = `
                        <div class="alert alert-success">
                            <strong>✅ ${data.message}</strong><br>
                            • Nowe modele: <strong>${data.new_models}</strong><br>
                            • Zaktualizowane: <strong>${data.updated_models}</strong><br>
                            • Łącznie: <strong>${data.total_models}</strong>
                        </div>
                    `;
                    result.style.display = 'block';
                    loadBrainData();
                } else {
                    throw new Error(data.error || 'Nieznany błąd');
                }
            } catch (e) {
                progress.style.display = 'none';
                result.innerHTML = `
                    <div class="alert alert-info">
                        <strong>❌ Błąd:</strong> ${e.message}
                    </div>
                `;
                result.style.display = 'block';
            } finally {
                btn.disabled = false;
                btn.innerText = '🌐 Importuj Modele z Matomo (1000+ modeli)';
            }
        }

        async function exportModels() {
            try {
                const res = await fetch('/admin/api/models/export');
                const data = await res.json();
                const blob = new Blob([JSON.stringify(data.models_data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `shark_models_${new Date().toISOString().split('T')[0]}.json`;
                a.click();
                alert(`✅ Wyeksportowano ${data.models_count} modeli!`);
            } catch (e) {
                alert('Błąd: ' + e.message);
            }
        }

        loadBrainData();
    </script>
</body>
</html>
"""

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

        for brand_data in devices_data:
            brand = brand_data.get('brand', 'Unknown')
            models = brand_data.get('models', [])

            for model_entry in models:
                model_name = model_entry.get('model')
                regex = model_entry.get('regex', '')

                if not model_name or not regex:
                    continue

                device_id = regex.replace('[', '').replace(']', '').replace('?', '')
                device_id = device_id.replace('(', '').replace(')', '').replace('|', '')
                device_id = device_id.split()[0] if ' ' in device_id else device_id
                device_id = device_id[:20]

                if not device_id:
                    continue

                full_name = f"{brand} {model_name}" if brand.lower() not in model_name.lower() else model_name

                if device_id not in EXTERNAL_DB:
                    EXTERNAL_DB[device_id] = full_name
                    new_models += 1
                elif EXTERNAL_DB[device_id] != full_name:
                    EXTERNAL_DB[device_id] = full_name
                    updated_models += 1

        logger.warning(f"⚠️ ADMIN: Matomo imported! New: {new_models}, Updated: {updated_models}")

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
