"""
SHARK v18 - Plik Konfiguracyjny
Centralne miejsce dla wszystkich ustawień aplikacji.
"""
import os
import logging

# --- Wersja Aplikacji ---
VERSION = "18.33"
VERSION_NAME = "Modular Architecture Refactor"

# --- Ustawienia Serwera ---
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5000))
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')

# --- Konfiguracja Bazy Danych ---
BRAIN_FILE = 'shark_brain_v18.json'
MAX_BRAIN_SIGNATURES = 10000
MAX_MODELS_PER_SIGNATURE = 5

# --- Konfiguracja MongoDB ---
MONGODB_URI = os.environ.get('MONGODB_URI', None)
MONGODB_DB = os.environ.get('MONGODB_DB', 'shark_db')
USE_MONGODB = MONGODB_URI is not None

# --- Konfiguracja Redis (dla Rate Limiter) ---
REDIS_URI = os.environ.get('REDIS_URI', None)
USE_REDIS = REDIS_URI is not None

# --- Konfiguracja Logowania ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('shark_app')