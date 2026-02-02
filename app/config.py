"""
SHARK v18 - Configuration Module
Centralna konfiguracja aplikacji, zmienne środowiskowe i stałe
"""
import os
import logging
from collections import deque

# Ładowanie zmiennych środowiskowych z pliku .env (jeśli istnieje)
if os.path.exists('.env'):
    print("[INFO] Loading environment variables from .env file...")
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
    print("[OK] Environment variables loaded from .env")

# --- MONGODB AVAILABILITY CHECK ---
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("[WARNING] PyMongo not installed. Using JSON file storage.")

# --- FILE PATHS ---
LOG_FILE = 'shark_logs_v18.csv'
BRAIN_FILE = 'shark_brain_v18.json'

# --- LIMITS ---
MAX_BRAIN_SIGNATURES = 10000
MAX_MODELS_PER_SIGNATURE = 5

# --- IN-MEMORY STORAGE ---
RECENT_LOGS = deque(maxlen=20)
BRAIN = {}
EXTERNAL_DB = {}

# --- LOGGING CONFIGURATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# --- MONGODB CONFIGURATION ---
MONGODB_URI = os.environ.get('MONGODB_URI', None)
MONGODB_DB = os.environ.get('MONGODB_DB', 'shark_db')
USE_MONGODB = MONGODB_AVAILABLE and MONGODB_URI

# --- FLASK CONFIGURATION ---
SECRET_KEY = os.environ.get('SECRET_KEY', 'shark-secret-key-v18-change-in-production')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5000))

# --- RATE LIMITING ---
RATE_LIMIT_ENABLED = True
RATE_LIMIT_DEFAULT = "100 per minute"
RATE_LIMIT_STORAGE_URL = "memory://"

# --- CORS CONFIGURATION ---
CORS_ORIGINS = "*"  # W produkcji zmień na konkretne domeny

# --- VERSION ---
VERSION = "v18.26"
VERSION_NAME = "BUGFIX: Show actual algorithm score instead of 0% for low confidence matches"
