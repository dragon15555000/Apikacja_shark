#!/usr/bin/env python3
"""
SHARK v18.33b - Modular Architecture
Główny plik startowy aplikacji Flask.
"""
import os
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- Krok 1: Ładowanie zmiennych środowiskowych ---
if os.path.exists('.env'):
    print("INFO: Loading environment variables from .env file...")
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
    print("INFO: Environment variables loaded.")

<<<<<<< Updated upstream
=======
# --- Krok 2: Import modułów aplikacji ---
>>>>>>> Stashed changes
import sys
from app.config import logger, VERSION, VERSION_NAME, HOST, PORT, DEBUG, USE_MONGODB, REDIS_URI, USE_REDIS
from app.database import init_db_connection, load_data, save_brain_atomic, BRAIN, EXTERNAL_DB, detection_logs_collection
from app.logic import parse_device_from_ua, find_top_3_matches
from app.models.accessory_codes import ACCESSORY_CODES

# --- Krok 3: Inicjalizacja Aplikacji Flask ---
app = Flask(__name__, template_folder='templates')
CORS(app)

# Wybór magazynu dla Rate Limiter
if USE_REDIS:
    storage_uri = REDIS_URI
    logger.info("🚦 Rate Limiter will use Redis storage.")
else:
    storage_uri = "memory://"
    logger.warning("🚦 Rate Limiter is using in-memory storage. This is not suitable for production with multiple workers.")

# Konfiguracja Rate Limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=storage_uri
)

# --- Krok 4: Dekorator Walidacji ---
def validate_json(*required_fields):
    """Decorator to validate JSON request data"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400
            try:
                data = request.json
                if data is None:
                    return jsonify({"error": "Request body cannot be empty"}), 400
            except Exception:
                return jsonify({"error": "Invalid JSON format"}), 400
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# GŁÓWNE ENDPOINTY APLIKACJI
# ============================================================================

@app.route('/')
def index():
    """Główna strona aplikacji."""
    return render_template('index.html')

@app.route('/version')
def version():
    """Endpoint diagnostyczny - sprawdź wersję kodu."""
    from app import logic
    has_find_top_3 = 'find_top_3_matches' in dir(logic)
    return jsonify({
        "version": VERSION,
        "version_name": VERSION_NAME,
        "python": sys.version,
        "has_find_top_3_matches": has_find_top_3,
        "mongodb": USE_MONGODB,
<<<<<<< Updated upstream
        "redis": USE_REDIS,
=======
>>>>>>> Stashed changes
        "collections_initialized": detection_logs_collection is not None
    })

@app.route('/api/check_brain', methods=['POST'])
@limiter.limit("30 per minute")
@validate_json('w', 'h', 'hz', 'gpu', 'canvasHash', 'dpr', 'ram', 'cores')
def check_brain():
    """Sprawdza fingerprint urządzenia w bazie danych."""
    try:
        d = request.json
        # Pobieranie i walidacja parametrów
        width = d.get('w')
        height = d.get('h')
        refresh_rate = d.get('hz')
        gpu = d.get('gpu')
        canvas_hash = d.get('canvasHash')
        dpr = d.get('dpr', 1.0)
        ram = d.get('ram', -1)
        cores = d.get('cores', -1)
        user_agent = d.get('userAgent', '')

<<<<<<< Updated upstream
        # Normalizacja viewportu
=======
        # Można dodać bardziej szczegółową walidację typów i zakresów, jeśli potrzeba

        # NORMALIZACJA VIEWPORT (zgodnie z wytycznymi)
        # Zaokraglaj szerokosc tylko jesli bardzo blisko calkowitej (blad renderowania <0.02px)
>>>>>>> Stashed changes
        exactWidth = round(width) if abs(width - round(width)) < 0.02 else width
        exactHeight = height

<<<<<<< Updated upstream
=======
        # Pobierz dodatkowe flagi z JavaScript (jesli dostepne)
        dprVerified = d.get('dprVerified', True)
        isZoomed = d.get('isZoomed', False)

>>>>>>> Stashed changes
        gpu_str = gpu[:50] if gpu else "None"
        logger.info(f"SCAN PARAMS: W={width}, H={height}, DPR={dpr}, RAM={ram}, Hz={refresh_rate}, GPU={gpu_str}")

        ua_id = parse_device_from_ua(user_agent)
        logger.info(f"PARSED UA_ID: {ua_id}")

        detection_log = {
            "ua_detected": ua_id,
            "ua_full": user_agent[:100] + "..." if len(user_agent) > 100 else user_agent,
            "fingerprint": f"{exactWidth}x{exactHeight} @ {dpr}x DPR, {refresh_rate}Hz, RAM: {ram}GB, Cores: {cores}, GPU: {gpu}",
            "canvas_hash": canvas_hash,
            "dpr": dpr,
            "ram": ram,
            "cores": cores
        }

        # Priorytet 1: User-Agent z dokładnym dopasowaniem w EXTERNAL_DB
        if ua_id:
            model_name = EXTERNAL_DB.get(ua_id)
            if model_name:
                logger.info(f"SUCCESS: Device identified via UA_EXACT: {model_name}")
                accessory_codes = ACCESSORY_CODES.get(model_name, {"screen": "N/A", "case": "N/A"})
                detection_log["method"] = "UA_EXACT"
                detection_log["matched_id"] = ua_id

                # Zapisz log do bazy
                if USE_MONGODB and detection_logs_collection is not None:
                    try:
                        detection_logs_collection.insert_one({
                            "timestamp": datetime.utcnow(), "status": "SUCCESS_UA", "model": model_name,
                            "confidence": 100, "method": "UA_EXACT", "ua_id": ua_id,
                            "fingerprint": f"{width}x{height} @ {dpr}x DPR", "gpu": gpu, "user_agent": user_agent[:200]
                        })
                    except Exception as e:
                        logger.error(f"Error saving detection log: {e}")

                return jsonify({
                    "found": True, "model": model_name, "confidence": 100, "source": "UA_EXACT",
                    "codes": accessory_codes, "detection_log": detection_log
                })

            # Priorytet 2: User-Agent wykryty, ale nie ma w bazie - zwróć surowy ID
            logger.info(f"SUCCESS: Device identified via UA_RAW: {ua_id}")
            detection_log["method"] = "UA_RAW"
            detection_log["matched_id"] = ua_id
<<<<<<< Updated upstream
=======

>>>>>>> Stashed changes
            if USE_MONGODB and detection_logs_collection is not None:
                try:
                    detection_logs_collection.insert_one({
                        "timestamp": datetime.utcnow(), "status": "SUCCESS_UA_RAW", "model": ua_id,
                        "confidence": 90, "method": "UA_CODE", "ua_id": ua_id,
                        "fingerprint": f"{width}x{height} @ {dpr}x DPR", "gpu": gpu, "user_agent": user_agent[:200]
                    })
                except Exception as e:
                    logger.error(f"Error saving detection log: {e}")

            return jsonify({
                "found": True, "model": ua_id, "confidence": 90, "source": "UA_CODE",
                "codes": {"screen": "N/A", "case": "N/A"}, "detection_log": detection_log
            })

        # Priorytet 3: Baza AI (fingerprint)
        dpr_rounded = round(float(dpr), 2)
        signature = f"{width}_{height}_{dpr_rounded}_{ram}_{refresh_rate}_{gpu}_{canvas_hash}"

        if signature in BRAIN:
            models = BRAIN[signature]
            top_model = max(models, key=models.get)
            total_count = sum(models.values())
            confidence = int((models[top_model] / total_count) * 100)
            logger.info(f"SUCCESS: Device identified via AI: {top_model} ({confidence}% confidence)")
            accessory_codes = ACCESSORY_CODES.get(top_model, {"screen": "N/A", "case": "N/A"})
            detection_log["method"] = "AI"
            detection_log["signature"] = signature
            detection_log["ai_models"] = dict(models)

            if USE_MONGODB and detection_logs_collection is not None:
<<<<<<< Updated upstream
                detection_logs_collection.insert_one({
                    "timestamp": datetime.utcnow(), "status": "SUCCESS_AI", "model": top_model,
                    "confidence": confidence, "method": "AI", "fingerprint": f"{width}x{height} @ {dpr}x DPR",
                    "gpu": gpu, "user_agent": user_agent[:200], "ai_models": dict(models)
                })
=======
                try:
                    detection_logs_collection.insert_one({
                        "timestamp": datetime.utcnow(),
                        "status": "SUCCESS_AI",
                        "model": top_model,
                        "confidence": confidence,
                        "method": "AI",
                        "fingerprint": f"{width}x{height} @ {dpr}x DPR, {refresh_rate}Hz, RAM: {ram}GB",
                        "gpu": gpu,
                        "user_agent": user_agent[:200],
                        "ai_models": dict(models)
                    })
                except Exception as e:
                    logger.error(f"Error saving detection log: {e}")
>>>>>>> Stashed changes

            return jsonify({
                "found": True, "model": top_model, "confidence": confidence, "source": "AI",
                "codes": accessory_codes, "detection_log": detection_log
            })

        # Priorytet 4: Heurystyka - znajdź 3 najlepiej dopasowane modele
        suggestions = find_top_3_matches(exactWidth, exactHeight, refresh_rate, gpu, dpr, ram, cores)

        if suggestions:
            detection_log["method"] = "HEURISTIC_TOP3"
            detection_log["suggestions"] = suggestions

            # AUTOMATYCZNA DECYZJA: Jeśli pierwszy model ma >=90% a drugi <60%, uznaj automatycznie
            if len(suggestions) >= 1:
                top_confidence = suggestions[0]["confidence"]
                second_confidence = suggestions[1]["confidence"] if len(suggestions) >= 2 else 0

                if top_confidence >= 90 and second_confidence < 60:
<<<<<<< Updated upstream
                    model_name = suggestions[0]["model"]
=======
                    # Pewność wystarczająco wysoka
                    model_name = suggestions[0]["model"]
                    # Usuń "(symulacja?)" z nazwy przy szukaniu kodów
>>>>>>> Stashed changes
                    clean_model_name = model_name.replace(" (symulacja?)", "")
                    accessory_codes = ACCESSORY_CODES.get(clean_model_name, {"screen": "N/A", "case": "N/A"})
                    logger.info(f"SUCCESS: Auto-decision made for {model_name} ({top_confidence}% vs {second_confidence}%)")

<<<<<<< Updated upstream
=======
                    # Zapisz log sukcesu
>>>>>>> Stashed changes
                    if USE_MONGODB and detection_logs_collection is not None:
                        detection_logs_collection.insert_one({
                            "timestamp": datetime.utcnow(), "status": "SUCCESS_AUTO", "model": model_name,
                            "confidence": top_confidence, "method": "HEURISTIC_AUTO",
                            "fingerprint": f"{width}x{height} @ {dpr}x DPR", "gpu": gpu, "user_agent": user_agent[:200]
                        })

                    return jsonify({
                        "found": True, "model": model_name, "confidence": top_confidence,
                        "source": "HEURISTIC_AUTO", "codes": accessory_codes,
                        "detection_log": detection_log, "auto_decision": True
                    })

            # Brak automatycznej decyzji - pokaż sugestie
            logger.info(f"FAILED: No exact match, suggesting top 3.")
<<<<<<< Updated upstream
=======

>>>>>>> Stashed changes
            if USE_MONGODB and detection_logs_collection is not None:
                detection_logs_collection.insert_one({
                    "timestamp": datetime.utcnow(), "status": "FAILED",
                    "suggestions": [s["model"] for s in suggestions[:3]],
                    "top_confidence": suggestions[0]["confidence"] if suggestions else 0,
                    "method": "HEURISTIC_SUGGESTIONS", "fingerprint": f"{width}x{height} @ {dpr}x DPR",
                    "gpu": gpu, "user_agent": user_agent[:200]
                })

            return jsonify({
                "found": False, "suggestions": suggestions,
                "codes": {"screen": "N/A", "case": "N/A"}, "detection_log": detection_log
            })

        logger.warning("FAILED: Device not found in any database.")
        detection_log["method"] = "NOT_FOUND"

        if USE_MONGODB and detection_logs_collection is not None:
            detection_logs_collection.insert_one({
                "timestamp": datetime.utcnow(), "status": "FAILED_NO_MATCH", "method": "NOT_FOUND",
                "fingerprint": f"{width}x{height} @ {dpr}x DPR", "gpu": gpu, "user_agent": user_agent[:200]
            })

        return jsonify({
            "found": False, "codes": {"screen": "N/A", "case": "N/A"}, "detection_log": detection_log
        })

    except Exception as e:
        logger.error(f"Error in check_brain: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/learn', methods=['POST'])
@limiter.limit("10 per minute")
@validate_json('w', 'h', 'hz', 'gpu', 'canvasHash', 'model', 'dpr', 'ram', 'cores')
def learn():
    """Uczy AI nowego fingerprintu urządzenia."""
    try:
        d = request.json
        model = d.get('model')
        if not isinstance(model, str) or len(model) > 100 or len(model) == 0:
            return jsonify({"error": "Invalid model value"}), 400

        # Tworzenie sygnatury
        width = d.get('w')
        height = d.get('h')
        refresh_rate = d.get('hz')
        gpu = d.get('gpu')
        canvas_hash = d.get('canvasHash')
        dpr_rounded = round(float(d.get('dpr', 1.0)), 2)
        ram = d.get('ram', -1)
        signature = f"{width}_{height}_{dpr_rounded}_{ram}_{refresh_rate}_{gpu}_{canvas_hash}"

        # Użyj nowej, atomowej funkcji zapisu
        success = save_brain_atomic(signature, {'model': model})
        if not success:
            return jsonify({"error": "Failed to save to brain"}), 500

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
<<<<<<< Updated upstream
        # Zapisz pusty słownik do bazy
        if USE_MONGODB and db:
            db['brain'].update_one({'_id': 'brain_v18'}, {'$set': {'data': {}}}, upsert=True)
        else:
            save_brain_atomic(None, None) # To powinno wyczyścić plik
=======
        save_brain_atomic(None, None) # To powinno wyczyścić
>>>>>>> Stashed changes
        logger.warning("ADMIN: Brain database cleared!")
        return jsonify({"status": "OK", "message": "Baza AI wyczyszczona!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

<<<<<<< Updated upstream
=======
@app.route('/admin/api/models/import-matomo', methods=['POST']) # Ta funkcja powinna być w osobnym skrypcie (np. setup_database.py)
def admin_import_matomo_models():
    """API: Importuj modele z Matomo Device Detector do EXTERNAL_DB."""
    try:
        import requests
        import yaml

        MATOMO_URL = "https://raw.githubusercontent.com/matomo-org/device-detector/master/regexes/device/mobiles.yml"

        logger.info("Pobieranie danych z Matomo...")
        response = requests.get(MATOMO_URL, timeout=30)
        response.raise_for_status()
        devices_data = yaml.safe_load(response.text)

        global EXTERNAL_DB
        new_models = 0
        updated_models = 0

        # Struktura Matomo YAML: {brand_name: {models: [...], device: ..., regex: ...}}
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

                device_id = regex.replace('[', '').replace(']', '').replace('?', '') # Uproszczone, może być niedokładne
                device_id = device_id.replace('(', '').replace(')', '').replace('|', '')
                device_id = device_id.replace('\\', '').replace('+', '').replace('.', '')
                device_id = device_id.split()[0] if ' ' in device_id else device_id
                device_id = device_id[:20].strip()

                if not device_id or len(device_id) < 2:
                    continue

                full_name = f"{brand} {model_name}" if brand.lower() not in model_name.lower() else model_name

                # Unikaj duplikatów
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

        # Zapisz do MongoDB
        if USE_MONGODB and external_db_collection is not None:
            try:
                external_db_collection.update_one(
                    {'_id': 'external_db'},
                    {'$set': {'data': EXTERNAL_DB, 'updated_at': datetime.utcnow()}},
                    upsert=True
                )
                logger.info(f"Saved {len(EXTERNAL_DB)} models to MongoDB!")
            except Exception as e:
                logger.error(f"Failed to save models to MongoDB: {e}")

        # Zapisz do pliku JSON (backup lokalny)
        external_db_file = 'shark_external_db.json'
        with open(external_db_file, 'w', encoding='utf-8') as f:
            json.dump(EXTERNAL_DB, f, indent=2, ensure_ascii=False)

        logger.warning(f"ADMIN: Matomo imported! New: {new_models}, Updated: {updated_models}")
        logger.info(f"Saved to MongoDB and {external_db_file}")

        return jsonify({
            "status": "OK",
            "message": f"Zaimportowano modele z Matomo!",
            "new_models": new_models,
            "updated_models": updated_models,
            "total_models": len(EXTERNAL_DB)
        })

    except Exception as e:
        logger.error(f"Błąd importu Matomo: {e}")
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
    """API: Pobierz wszystkie zweryfikowane modele z bazy."""
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
    """API: Dodaj nowy zweryfikowany model do bazy."""
    try:
        data = request.json
        required_fields = ['name', 'system_name', 'w', 'h', 'dpr', 'ram', 'hz', 'gpu']

        for field in required_fields:
            if field not in data:
                return jsonify({"status": "ERROR", "error": f"Missing field: {field}"}), 400

        if USE_MONGODB and verified_models_collection is not None:
            # Sprawdź czy model już istnieje
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
    """API: Aktualizuj zweryfikowany model w bazie."""
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
    """API: Usuń zweryfikowany model z bazy."""
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

>>>>>>> Stashed changes
@app.route('/admin/api/detection-logs', methods=['GET'])
def admin_get_detection_logs():
    """API: Pobierz logi rozpoznań (sukces i porażka)."""
    try:
        if USE_MONGODB and detection_logs_collection is not None:
<<<<<<< Updated upstream
            limit = int(request.args.get('limit', 200))
            logs = list(detection_logs_collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(limit))
=======
            # Pobierz ostatnie 100 logów
            logs = list(detection_logs_collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(200))
>>>>>>> Stashed changes

            # Statystyki
            total_logs = detection_logs_collection.count_documents({})
            success_count = detection_logs_collection.count_documents({'status': {'$regex': '^SUCCESS'}})
            failed_count = detection_logs_collection.count_documents({'status': {'$regex': '^FAILED'}})

            return jsonify({
                "status": "OK", "logs": logs,
                "stats": {
                    "total": total_logs, "success": success_count, "failed": failed_count,
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
    """API: Wyczyść logi rozpoznań."""
    try:
        if USE_MONGODB and detection_logs_collection is not None:
            result = detection_logs_collection.delete_many({})
            logger.warning(f"ADMIN: Detection logs cleared! Deleted {result.deleted_count} logs")
            return jsonify({"status": "OK", "message": f"Usunięto {result.deleted_count} logów!"})
        else:
            return jsonify({"status": "ERROR", "error": "MongoDB not available"}), 500
    except Exception as e:
        logger.error(f"Error clearing detection logs: {e}")
        return jsonify({"status": "ERROR", "error": str(e)}), 500

<<<<<<< Updated upstream
=======
@app.route('/admin/api/sync-to-mongodb', methods=['POST'])
def admin_sync_to_mongodb():
    """API: Synchronizuj wszystkie dane do MongoDB."""
    try:
        if not USE_MONGODB:
            error_msg = "MongoDB nie jest dostępne. Ustaw zmienne środowiskowe MONGODB_URI i MONGODB_DB."
            return jsonify({
                "status": "ERROR",
                "error": error_msg,
                "help": "Lokalnie: ustaw zmienne w pliku .env lub systemowo. Na Render: zmienne są już ustawione."
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
            logger.info(f"Static Identifiers synced: {len(STATIC_IDENTIFIERS)} models")
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
            logger.info(f"Android Identifiers synced: {len(ANDROID_IDENTIFIERS)} models")
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
            logger.info(f"Accessory Codes synced: {len(ACCESSORY_CODES)} models")
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
            logger.info(f"External DB synced: {len(EXTERNAL_DB)} models")
        except Exception as e:
            results['external_db'] = f"ERROR: {e}"

        # 5. Synchronizuj BRAIN (już istnieje, ale dla pewności)
        try:
            brain_collection.update_one(
                {'_id': 'brain_v18'},
                {'$set': {'data': BRAIN, 'updated_at': datetime.utcnow()}},
                upsert=True
            )
            results['brain'] = len(BRAIN)
            logger.info(f"Brain synced: {len(BRAIN)} signatures")
        except Exception as e:
            results['brain'] = f"ERROR: {e}"

        logger.warning(f"ADMIN: All data synced to MongoDB!")
        return jsonify({
            "status": "OK",
            "message": "Wszystkie dane zsynchronizowane do MongoDB!",
            "results": results
        })

    except Exception as e:
        logger.error(f"Error syncing to MongoDB: {e}")
        return jsonify({"status": "ERROR", "error": str(e)}), 500

>>>>>>> Stashed changes
# --- Krok 5: Główna funkcja uruchomieniowa ---
if __name__ == '__main__':
    logger.info(f"🚀 Starting SHARK {VERSION} - {VERSION_NAME}")
    init_db_connection()
    load_data()

    print(f"\n{'='*60}")
    print(f"SHARK v18 Server is running!")
    print(f"URL: http://{HOST}:{PORT}")
    print(f"Storage: {'MongoDB' if USE_MONGODB else 'JSON File'}")
    print(f"Brain Signatures: {len(BRAIN)}")
    print(f"{'='*60}\n")

    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
        threaded=True
    )
