import json
import logging
import os
import socket
import threading
import webbrowser
import re
from collections import deque
from datetime import datetime
from functools import wraps
import qrcode
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- KONFIGURACJA ---
LOG_FILE = 'shark_logs_v18.csv'
BRAIN_FILE = 'shark_brain_v18.json'
MAX_BRAIN_SIGNATURES = 10000  # Limit rozmiaru BRAIN (zapobieganie memory leak)
MAX_MODELS_PER_SIGNATURE = 5  # Max modeli na sygnaturę

RECENT_LOGS = deque(maxlen=20)
LOGS_LOCK = threading.Lock()
BRAIN_LOCK = threading.Lock()  # Lock dla thread-safe operacji na BRAIN
BRAIN = {}
EXTERNAL_DB = {}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

STATIC_IDENTIFIERS = {
    "iPhone18,1": "iPhone 17 Pro",
    "iPhone18,2": "iPhone 17 Pro Max",
    "iPhone18,3": "iPhone 17",
    "iPhone18,4": "iPhone Air",
    "iPhone17,1": "iPhone 16 Pro",
    "iPhone17,2": "iPhone 16 Pro Max",
    "iPhone17,3": "iPhone 16",
    "iPhone17,4": "iPhone 16 Plus",
    "iPhone17,5": "iPhone 16e",
    "iPhone16,1": "iPhone 15 Pro",
    "iPhone16,2": "iPhone 15 Pro Max",
    "iPhone15,4": "iPhone 15",
    "iPhone15,5": "iPhone 15 Plus",
    "iPhone15,2": "iPhone 14 Pro",
    "iPhone15,3": "iPhone 14 Pro Max",
    "iPhone14,7": "iPhone 14",
    "iPhone14,8": "iPhone 14 Plus",
    "iPhone14,5": "iPhone 13",
    "iPhone14,2": "iPhone 13 Pro",
    "iPhone14,3": "iPhone 13 Pro Max",
    "iPhone13,2": "iPhone 12",
    "iPhone13,3": "iPhone 12 Pro",
    "iPhone13,4": "iPhone 12 Pro Max",
    "iPhone12,1": "iPhone 11",
    "iPhone12,3": "iPhone 11 Pro",
    "iPhone12,5": "iPhone 11 Pro Max"
}

# ANDROID DEVICE IDENTIFIERS - Mapowanie modeli Android
ANDROID_IDENTIFIERS = {
    # Samsung Galaxy S Series
    "SM-S928": "Samsung Galaxy S24 Ultra",
    "SM-S926": "Samsung Galaxy S24+",
    "SM-S921": "Samsung Galaxy S24",
    "SM-S918": "Samsung Galaxy S23 Ultra",
    "SM-S916": "Samsung Galaxy S23+",
    "SM-S911": "Samsung Galaxy S23",
    "SM-S908": "Samsung Galaxy S22 Ultra",
    "SM-S906": "Samsung Galaxy S22+",
    "SM-S901": "Samsung Galaxy S22",
    "SM-G998": "Samsung Galaxy S21 Ultra",
    "SM-G996": "Samsung Galaxy S21+",
    "SM-G991": "Samsung Galaxy S21",
    "SM-G988": "Samsung Galaxy S20 Ultra",
    "SM-G986": "Samsung Galaxy S20+",
    "SM-G981": "Samsung Galaxy S20",

    # Samsung Galaxy A Series
    "SM-A546": "Samsung Galaxy A54",
    "SM-A536": "Samsung Galaxy A53",
    "SM-A526": "Samsung Galaxy A52",
    "SM-A346": "Samsung Galaxy A34",
    "SM-A336": "Samsung Galaxy A33",

    # Samsung Galaxy Z Series (Foldables)
    "SM-F946": "Samsung Galaxy Z Fold 5",
    "SM-F936": "Samsung Galaxy Z Fold 4",
    "SM-F926": "Samsung Galaxy Z Fold 3",
    "SM-F741": "Samsung Galaxy Z Flip 5",
    "SM-F721": "Samsung Galaxy Z Flip 4",
    "SM-F711": "Samsung Galaxy Z Flip 3",

    # Google Pixel
    "Pixel 8 Pro": "Google Pixel 8 Pro",
    "Pixel 8": "Google Pixel 8",
    "Pixel 7 Pro": "Google Pixel 7 Pro",
    "Pixel 7": "Google Pixel 7",
    "Pixel 6 Pro": "Google Pixel 6 Pro",
    "Pixel 6": "Google Pixel 6",
    "Pixel 5": "Google Pixel 5",

    # Xiaomi
    "2311DRK48C": "Xiaomi 14 Pro",
    "23117PN0CC": "Xiaomi 14",
    "2304FPN6DC": "Xiaomi 13 Ultra",
    "2211133C": "Xiaomi 13 Pro",
    "2211133G": "Xiaomi 13",
    "2206123SC": "Xiaomi 12 Pro",
    "2201123G": "Xiaomi 12",
    "M2102K1G": "Xiaomi Mi 11",
    "M2007J20CG": "Xiaomi Mi 10T Pro",

    # OnePlus
    "CPH2581": "OnePlus 12",
    "CPH2449": "OnePlus 11",
    "NE2213": "OnePlus 10 Pro",
    "LE2123": "OnePlus 9 Pro",
    "LE2121": "OnePlus 9",
    "IN2023": "OnePlus 8 Pro",
    "IN2020": "OnePlus 8",

    # Huawei
    "ALN-L29": "Huawei P40 Pro",
    "ANA-NX9": "Huawei P40",
    "VOG-L29": "Huawei P30 Pro",
    "ELE-L29": "Huawei P30",
    "MAR-LX1A": "Huawei P Smart 2019",
}

# KODY AKCESORIÓW - Mapowanie modeli na kody magazynowe
ACCESSORY_CODES = {
    # iPhone
    "iPhone 17 Pro Max": {"screen": "A1U1", "case": "A1U2"},
    "iPhone 17 Pro": {"screen": "A2U1", "case": "A2U2"},
    "iPhone 17": {"screen": "A3U1", "case": "A3U2"},
    "iPhone Air": {"screen": "A4U1", "case": "A4U2"},
    "iPhone 16 Pro Max": {"screen": "B1U1", "case": "B1U2"},
    "iPhone 16 Pro": {"screen": "B2U1", "case": "B2U2"},
    "iPhone 16": {"screen": "B3U1", "case": "B3U2"},
    "iPhone 16 Plus": {"screen": "B4U1", "case": "B4U2"},
    "iPhone 16e": {"screen": "B5U1", "case": "B5U2"},
    "iPhone 15 Pro Max": {"screen": "C1U1", "case": "C1U2"},
    "iPhone 15 Pro": {"screen": "C2U1", "case": "C2U2"},
    "iPhone 15": {"screen": "C3U1", "case": "C3U2"},
    "iPhone 15 Plus": {"screen": "C4U1", "case": "C4U2"},
    "iPhone 14 Pro Max": {"screen": "D1U1", "case": "D1U2"},
    "iPhone 14 Pro": {"screen": "D2U1", "case": "D2U2"},
    "iPhone 14": {"screen": "D3U1", "case": "D3U2"},
    "iPhone 14 Plus": {"screen": "D4U1", "case": "D4U2"},
    "iPhone 13 Pro Max": {"screen": "E1U1", "case": "E1U2"},
    "iPhone 13 Pro": {"screen": "E2U1", "case": "E2U2"},
    "iPhone 13": {"screen": "E3U1", "case": "E3U2"},
    "iPhone 12 Pro Max": {"screen": "F1U1", "case": "F1U2"},
    "iPhone 12 Pro": {"screen": "F2U1", "case": "F2U2"},
    "iPhone 12": {"screen": "F3U1", "case": "F3U2"},
    "iPhone 11 Pro Max": {"screen": "G1U1", "case": "G1U2"},
    "iPhone 11 Pro": {"screen": "G2U1", "case": "G2U2"},
    "iPhone 11": {"screen": "G3U1", "case": "G3U2"},

    # Samsung Galaxy S Series
    "Samsung Galaxy S24 Ultra": {"screen": "SA1U1", "case": "SA1U2"},
    "Samsung Galaxy S24+": {"screen": "SA2U1", "case": "SA2U2"},
    "Samsung Galaxy S24": {"screen": "SA3U1", "case": "SA3U2"},
    "Samsung Galaxy S23 Ultra": {"screen": "SB1U1", "case": "SB1U2"},
    "Samsung Galaxy S23+": {"screen": "SB2U1", "case": "SB2U2"},
    "Samsung Galaxy S23": {"screen": "SB3U1", "case": "SB3U2"},
    "Samsung Galaxy S22 Ultra": {"screen": "SC1U1", "case": "SC1U2"},
    "Samsung Galaxy S22+": {"screen": "SC2U1", "case": "SC2U2"},
    "Samsung Galaxy S22": {"screen": "SC3U1", "case": "SC3U2"},
    "Samsung Galaxy S21 Ultra": {"screen": "SD1U1", "case": "SD1U2"},
    "Samsung Galaxy S21+": {"screen": "SD2U1", "case": "SD2U2"},
    "Samsung Galaxy S21": {"screen": "SD3U1", "case": "SD3U2"},
    "Samsung Galaxy S20 Ultra": {"screen": "SE1U1", "case": "SE1U2"},
    "Samsung Galaxy S20+": {"screen": "SE2U1", "case": "SE2U2"},
    "Samsung Galaxy S20": {"screen": "SE3U1", "case": "SE3U2"},

    # Samsung Galaxy A Series
    "Samsung Galaxy A54": {"screen": "AA1U1", "case": "AA1U2"},
    "Samsung Galaxy A53": {"screen": "AA2U1", "case": "AA2U2"},
    "Samsung Galaxy A52": {"screen": "AA3U1", "case": "AA3U2"},
    "Samsung Galaxy A34": {"screen": "AA4U1", "case": "AA4U2"},
    "Samsung Galaxy A33": {"screen": "AA5U1", "case": "AA5U2"},

    # Samsung Galaxy Z Series
    "Samsung Galaxy Z Fold 5": {"screen": "ZF1U1", "case": "ZF1U2"},
    "Samsung Galaxy Z Fold 4": {"screen": "ZF2U1", "case": "ZF2U2"},
    "Samsung Galaxy Z Fold 3": {"screen": "ZF3U1", "case": "ZF3U2"},
    "Samsung Galaxy Z Flip 5": {"screen": "ZP1U1", "case": "ZP1U2"},
    "Samsung Galaxy Z Flip 4": {"screen": "ZP2U1", "case": "ZP2U2"},
    "Samsung Galaxy Z Flip 3": {"screen": "ZP3U1", "case": "ZP3U2"},

    # Google Pixel
    "Google Pixel 8 Pro": {"screen": "GP1U1", "case": "GP1U2"},
    "Google Pixel 8": {"screen": "GP2U1", "case": "GP2U2"},
    "Google Pixel 7 Pro": {"screen": "GP3U1", "case": "GP3U2"},
    "Google Pixel 7": {"screen": "GP4U1", "case": "GP4U2"},
    "Google Pixel 6 Pro": {"screen": "GP5U1", "case": "GP5U2"},
    "Google Pixel 6": {"screen": "GP6U1", "case": "GP6U2"},
    "Google Pixel 5": {"screen": "GP7U1", "case": "GP7U2"},

    # Xiaomi
    "Xiaomi 14 Pro": {"screen": "XM1U1", "case": "XM1U2"},
    "Xiaomi 14": {"screen": "XM2U1", "case": "XM2U2"},
    "Xiaomi 13 Ultra": {"screen": "XM3U1", "case": "XM3U2"},
    "Xiaomi 13 Pro": {"screen": "XM4U1", "case": "XM4U2"},
    "Xiaomi 13": {"screen": "XM5U1", "case": "XM5U2"},
    "Xiaomi 12 Pro": {"screen": "XM6U1", "case": "XM6U2"},
    "Xiaomi 12": {"screen": "XM7U1", "case": "XM7U2"},
    "Xiaomi Mi 11": {"screen": "XM8U1", "case": "XM8U2"},
    "Xiaomi Mi 10T Pro": {"screen": "XM9U1", "case": "XM9U2"},

    # OnePlus
    "OnePlus 12": {"screen": "OP1U1", "case": "OP1U2"},
    "OnePlus 11": {"screen": "OP2U1", "case": "OP2U2"},
    "OnePlus 10 Pro": {"screen": "OP3U1", "case": "OP3U2"},
    "OnePlus 9 Pro": {"screen": "OP4U1", "case": "OP4U2"},
    "OnePlus 9": {"screen": "OP5U1", "case": "OP5U2"},
    "OnePlus 8 Pro": {"screen": "OP6U1", "case": "OP6U2"},
    "OnePlus 8": {"screen": "OP7U1", "case": "OP7U2"},

    # Huawei
    "Huawei P40 Pro": {"screen": "HW1U1", "case": "HW1U2"},
    "Huawei P40": {"screen": "HW2U1", "case": "HW2U2"},
    "Huawei P30 Pro": {"screen": "HW3U1", "case": "HW3U2"},
    "Huawei P30": {"screen": "HW4U1", "case": "HW4U2"},
    "Huawei P Smart 2019": {"screen": "HW5U1", "case": "HW5U2"},
}

def load_data():
    """Load brain data from JSON file with thread safety."""
    global BRAIN, EXTERNAL_DB
    try:
        if os.path.exists(BRAIN_FILE):
            with open(BRAIN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with BRAIN_LOCK:
                BRAIN = data
            logger.info(f"Brain loaded: {len(BRAIN)} signatures")
    except Exception as e:
        logger.error(f"Error loading brain: {e}")
        with BRAIN_LOCK:
            BRAIN = {}

    # Merge iOS and Android identifiers
    EXTERNAL_DB = {**STATIC_IDENTIFIERS, **ANDROID_IDENTIFIERS}

def save_brain():
    """Save brain data to JSON file with atomic write and thread safety."""
    try:
        temp = f"{BRAIN_FILE}.tmp"

        with BRAIN_LOCK:
            brain_copy = BRAIN.copy()

        with open(temp, 'w', encoding='utf-8') as f:
            json.dump(brain_copy, f, indent=2)

        os.replace(temp, BRAIN_FILE)
        logger.info(f"Brain saved: {len(brain_copy)} signatures")
    except Exception as e:
        logger.error(f"Error saving brain: {e}")

def parse_device_from_ua(ua):
    """Parse device identifier from User-Agent string (iOS and Android)"""
    if not ua or not isinstance(ua, str):
        return None

    # Limit UA length to prevent regex DoS
    if len(ua) > 1000:
        ua = ua[:1000]

    try:
        # iOS devices
        match = re.search(r'iPhone(\d+,\d+)', ua)
        if match:
            return "iPhone" + match.group(1)
        match_ipad = re.search(r'iPad(\d+,\d+)', ua)
        if match_ipad:
            return "iPad" + match_ipad.group(1)

        # Android devices - Samsung
        match_samsung = re.search(r'(SM-[A-Z]\d{3}[A-Z]?)', ua)
        if match_samsung:
            model_code = match_samsung.group(1)[:7]  # Limit to SM-XXXX
            return model_code

        # Android devices - Google Pixel
        match_pixel = re.search(r'(Pixel \d+(?:\s+Pro)?)', ua)
        if match_pixel:
            return match_pixel.group(1)

        # Android devices - Xiaomi (Build codes)
        match_xiaomi = re.search(r'Build/([A-Z0-9]{10,})', ua)
        if match_xiaomi and 'Xiaomi' in ua:
            build_code = match_xiaomi.group(1)[:12]
            return build_code

        # Android devices - OnePlus
        match_oneplus = re.search(r'((?:CPH|LE|IN|NE)\d{4})', ua)
        if match_oneplus:
            return match_oneplus.group(1)

        # Android devices - Huawei
        match_huawei = re.search(r'([A-Z]{3}-[A-Z0-9]{3,5})', ua)
        if match_huawei and ('HUAWEI' in ua.upper() or 'HONOR' in ua.upper()):
            return match_huawei.group(1)

    except Exception as e:
        logger.error(f"Error parsing UA: {e}")

    return None

app = Flask(__name__)
CORS(app)

# Rate Limiter Configuration
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
    <title>SHARK v18 Final</title>
    <title>SHARK v18.26</title>
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
    <div class="header"><h1>SHARK v18</h1><div class="status">ONLINE • HTTPS</div></div>
    <div class="header"><h1>SHARK v18.26</h1><div class="status">ONLINE • HTTPS</div></div>
    <div id="result-hero"><div class="model-name" id="displayModel">...</div><div class="conf-badge" id="displayConf">...</div></div>
    <div class="container">
        <div class="ios-group"><div style="padding: 15px;"><button id="scanBtn" class="btn-scan" onclick="startSharkScan()">🚀 Rozpocznij Skanowanie</button></div></div>

        <div id="codesSection" style="display:none;">
            <div class="code-box">
                <div class="code-label">📱 Kod Szybki</div>
                <div class="code-value" id="codeScreen">-</div>
                <div class="code-desc">Podaj ten kod sprzedawcy</div>
            </div>
            <div class="group-title">Dostępne Akcesoria</div>
            <div class="ios-group">
                <div class="row"><span>🛡️ Szkło Ochronne</span><span class="val strong" id="codeScreenDetail">-</span></div>
                <div class="row"><span>📦 Etui</span><span class="val strong" id="codeCase">-</span></div>
            </div>
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
            <select id="modelSelector"></select><button class="btn-fix" onclick="teachBrain()">Zapisz i Naucz AI</button>
        </div>
    </div>
<script>
    const DB_HEURISTIC = [
        // iPhone
        {name:"iPhone 17 Pro Max",w:440,h:956,hz:120,gpu:"a19"}, {name:"iPhone 17 Pro",w:402,h:874,hz:120,gpu:"a19"},
        {name:"iPhone 16 Pro Max",w:440,h:956,hz:120,gpu:"a18"}, {name:"iPhone 16 Pro",w:402,h:874,hz:120,gpu:"a18"},
        {name:"iPhone 16 / Plus",w:393,h:852,hz:60,gpu:"a18"}, {name:"iPhone 15 Pro Max",w:430,h:932,hz:120,gpu:"a17"},
        {name:"iPhone 15 Pro",w:393,h:852,hz:120,gpu:"a17"}, {name:"iPhone 15 / Plus",w:393,h:852,hz:60,gpu:"a16"},
        {name:"iPhone 14 Pro Max",w:430,h:932,hz:120,gpu:"a16"}, {name:"iPhone 14 Pro",w:393,h:852,hz:120,gpu:"a16"},
        {name:"iPhone 13 Pro Max",w:428,h:926,hz:120,gpu:"a15"}, {name:"iPhone 13 / 14",w:390,h:844,hz:60,gpu:"a15"},
        {name:"iPhone 12 / Pro",w:390,h:844,hz:60,gpu:"a14"}, {name:"iPhone 11",w:414,h:896,hz:60,gpu:"a13"},
        // Samsung Galaxy S Series
        {name:"Samsung Galaxy S24 Ultra",w:412,h:915,hz:120,gpu:"adreno"}, {name:"Samsung Galaxy S24+",w:384,h:854,hz:120,gpu:"adreno"},
        {name:"Samsung Galaxy S24",w:360,h:780,hz:120,gpu:"adreno"}, {name:"Samsung Galaxy S23 Ultra",w:412,h:915,hz:120,gpu:"adreno"},
        {name:"Samsung Galaxy S23+",w:384,h:854,hz:120,gpu:"adreno"}, {name:"Samsung Galaxy S23",w:360,h:780,hz:120,gpu:"adreno"},
        {name:"Samsung Galaxy S22 Ultra",w:412,h:915,hz:120,gpu:"adreno"}, {name:"Samsung Galaxy S22+",w:384,h:854,hz:120,gpu:"adreno"},
        {name:"Samsung Galaxy S22",w:360,h:780,hz:120,gpu:"adreno"}, {name:"Samsung Galaxy S21 Ultra",w:412,h:915,hz:120,gpu:"mali"},
        {name:"Samsung Galaxy S21+",w:384,h:854,hz:120,gpu:"mali"}, {name:"Samsung Galaxy S21",w:360,h:780,hz:120,gpu:"mali"},
        {name:"Samsung Galaxy S20 Ultra",w:412,h:915,hz:120,gpu:"mali"}, {name:"Samsung Galaxy S20+",w:384,h:854,hz:120,gpu:"mali"},
        {name:"Samsung Galaxy S20",w:360,h:800,hz:120,gpu:"mali"},
        // Samsung Galaxy A Series
        {name:"Samsung Galaxy A54",w:412,h:914,hz:120,gpu:"adreno"}, {name:"Samsung Galaxy A53",w:412,h:914,hz:120,gpu:"adreno"},
        {name:"Samsung Galaxy A52",w:412,h:914,hz:90,gpu:"adreno"}, {name:"Samsung Galaxy A34",w:412,h:914,hz:120,gpu:"mali"},
        {name:"Samsung Galaxy A33",w:412,h:914,hz:90,gpu:"mali"},
        // Google Pixel
        {name:"Google Pixel 8 Pro",w:412,h:915,hz:120,gpu:"mali"}, {name:"Google Pixel 8",w:412,h:915,hz:120,gpu:"mali"},
        {name:"Google Pixel 7 Pro",w:412,h:915,hz:120,gpu:"mali"}, {name:"Google Pixel 7",w:412,h:915,hz:90,gpu:"mali"},
        {name:"Google Pixel 6 Pro",w:412,h:915,hz:120,gpu:"mali"}, {name:"Google Pixel 6",w:412,h:915,hz:90,gpu:"mali"},
        {name:"Google Pixel 5",w:393,h:851,hz:90,gpu:"adreno"},
        // Xiaomi
        {name:"Xiaomi 14 Pro",w:412,h:915,hz:120,gpu:"adreno"}, {name:"Xiaomi 14",w:412,h:915,hz:120,gpu:"adreno"},
        {name:"Xiaomi 13 Ultra",w:412,h:915,hz:120,gpu:"adreno"}, {name:"Xiaomi 13 Pro",w:412,h:915,hz:120,gpu:"adreno"},
        {name:"Xiaomi 13",w:412,h:915,hz:120,gpu:"adreno"}, {name:"Xiaomi 12 Pro",w:412,h:915,hz:120,gpu:"adreno"},
        {name:"Xiaomi 12",w:412,h:915,hz:120,gpu:"adreno"}, {name:"Xiaomi Mi 11",w:412,h:915,hz:120,gpu:"adreno"},
        // OnePlus
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
        console.log("🎯 Best match:",best.name,"Score:",best.score);
        showResult(best.name,best.score,false);
    }
    function showResult(m,c,ai){const d=document.getElementById('displayModel'),b=document.getElementById('displayConf');d.innerText=m;b.innerText=ai?`🧠 PEWNOŚĆ: ${c}%`:`⚙️ ALGORYTM: ${c}%`;b.style.background=ai?'#eef5ff':'#f2f2f7';b.style.color=ai?'#007aff':'#8e8e93';const sel=document.getElementById('modelSelector');for(let i=0;i<sel.options.length;i++)if(sel.options[i].value===m){sel.selectedIndex=i;break;}}
    function showCodes(codes){
        if(!codes || (!codes.screen && !codes.case)) return;
        document.getElementById('codesSection').style.display='block';
        document.getElementById('codeScreen').innerText=codes.screen || 'N/A';
        document.getElementById('codeScreenDetail').innerText=codes.screen || 'N/A';
        document.getElementById('codeCase').innerText=codes.case || 'N/A';
    }
    async function teachBrain(){if(!currentScanData)return;currentScanData.model=document.getElementById('modelSelector').value;await fetch('/api/learn',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(currentScanData)});alert("✅ Nauczono!");showResult(currentScanData.model,100,true);}
</script></body></html>
"""

# Validation decorator
def validate_json(*required_fields):
    """Decorator to validate JSON request data"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                logger.warning(f"Invalid content-type for {request.path}")
                return jsonify({"error": "Content-Type must be application/json"}), 400

            try:
                data = request.json
            except Exception as e:
                logger.error(f"JSON parsing error: {e}")
                return jsonify({"error": "Invalid JSON format"}), 400

            if data is None:
                logger.warning(f"Empty JSON body for {request.path}")
                return jsonify({"error": "Request body cannot be empty"}), 400

            # Check required fields
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logger.warning(f"Missing fields: {missing_fields}")
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

        # Validate data types and ranges
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

        with BRAIN_LOCK:
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

        # Validate data types and ranges
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

        with BRAIN_LOCK:
            # Sprawdź limit rozmiaru BRAIN
            if signature not in BRAIN and len(BRAIN) >= MAX_BRAIN_SIGNATURES:
                # Usuń najstarszą sygnaturę (pierwszą w dict)
                oldest_signature = next(iter(BRAIN))
                del BRAIN[oldest_signature]
                logger.warning(
                    f"Brain limit reached. Removed oldest signature: "
                    f"{oldest_signature[:50]}..."
                )

            if signature not in BRAIN:
                BRAIN[signature] = {}

            # Sprawdź limit modeli na sygnaturę
            if (model not in BRAIN[signature] and
                    len(BRAIN[signature]) >= MAX_MODELS_PER_SIGNATURE):
                # Usuń model z najmniejszą liczbą wystąpień
                min_model = min(BRAIN[signature], key=BRAIN[signature].get)
                del BRAIN[signature][min_model]
                logger.warning(
                    f"Model limit reached for signature. Removed: {min_model}"
                )

            if model not in BRAIN[signature]:
                BRAIN[signature][model] = 0

            BRAIN[signature][model] += 1

        save_brain()

        with LOGS_LOCK:
            RECENT_LOGS.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "model": model,
                "type": "LEARNED"
            })

        logger.info(f"AI learned: {model} (signature: {signature[:50]}...)")
        return jsonify({
            "status": "OK",
            "message": "Model learned successfully"
        })

    except Exception as e:
        logger.error(f"Error in learn: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

def get_ip():
    """Get local IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == '__main__':
    load_data()
    ip = get_ip()
    url = f"https://{ip}:5000"

    print(f"\n{'='*60}")
    print(f"SHARK v18 FINAL | URL: {url}")
    print(f"SHARK v18.26 | URL: {url}")
    print(f"Brain signatures: {len(BRAIN)}")
    print(f"Max signatures: {MAX_BRAIN_SIGNATURES}")
    print(f"{'='*60}\n")

    threading.Timer(1.5, lambda: webbrowser.open(url)).start()

    try:
        qr = qrcode.QRCode()
        qr.add_data(url)
        qr.print_ascii()
    except Exception as e:
        logger.error(f"QR code generation failed: {e}")

    app.run(
        host='0.0.0.0',
        port=5000,
        ssl_context='adhoc',
        debug=False,
        threaded=True
    )
