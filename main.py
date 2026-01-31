#!/usr/bin/env python3
"""
SHARK v18.23 - REFACTORED VERSION
Main entry point - modular architecture
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sys

# Import konfiguracji
from app.config import VERSION, VERSION_NAME, HOST, PORT, DEBUG, USE_MONGODB, logger

# Import bazy danych
from app.database import init_mongodb, load_data

# Import modeli
from app.models import HEURISTIC_DB, STATIC_IDENTIFIERS, ANDROID_IDENTIFIERS, ACCESSORY_CODES

# Import logiki
from app.utils.logic import parse_device_from_ua, find_top_3_matches

# Import walidatorów
from app.utils.validators import validate_json

# Inicjalizacja Flask
app = Flask(__name__, template_folder='templates')
CORS(app)

# Rate Limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Inicjalizacja MongoDB
logger.info("🚀 Starting SHARK v18 - Refactored Version")
init_mongodb()
load_data()

# Import i rejestracja route'ów
# UWAGA: Importujemy TUTAJ, żeby app był już zdefiniowany
from app.routes.api_routes import register_api_routes
from app.routes.admin_routes import register_admin_routes

register_api_routes(app, limiter)
register_admin_routes(app)

# Podstawowe route'y
@app.route('/')
def index():
    """Serve main HTML page."""
    return render_template('index.html')

@app.route('/version')
def version():
    """Endpoint diagnostyczny - sprawdź wersję kodu."""
    has_find_top_3 = 'find_top_3_matches' in dir(sys.modules['app.utils.logic'])
    from app.database import detection_logs_collection

    return jsonify({
        "version": VERSION,
        "version_name": VERSION_NAME,
        "python": sys.version,
        "has_find_top_3_matches": has_find_top_3,
        "mongodb": USE_MONGODB,
        "collections_initialized": detection_logs_collection is not None if USE_MONGODB else False,
        "heuristic_db_size": len(HEURISTIC_DB),
        "architecture": "MODULAR_REFACTORED"
    })

if __name__ == '__main__':
    logger.info(f"🌐 Starting Flask server on {HOST}:{PORT}")
    logger.info(f"📦 Loaded {len(HEURISTIC_DB)} models in HEURISTIC_DB")
    logger.info(f"🔧 Debug mode: {DEBUG}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
