"""
SHARK v18 - API Routes
Główne endpointy API: /api/check_brain, /api/learn
"""
from flask import request, jsonify
from datetime import datetime
from app.config import USE_MONGODB, BRAIN, EXTERNAL_DB, MAX_BRAIN_SIGNATURES, MAX_MODELS_PER_SIGNATURE, logger
from app.models.identifiers import STATIC_IDENTIFIERS, ANDROID_IDENTIFIERS, ACCESSORY_CODES
from app.utils.logic import parse_device_from_ua, find_top_3_matches
from app.utils.validators import validate_json
from app.database import detection_logs_collection, save_brain, save_brain_signature

def register_api_routes(app, limiter):
    """Rejestruje główne endpointy API"""

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

            # Walidacja
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

            # NORMALIZACJA VIEWPORT
            exactWidth = round(width) if abs(width - round(width)) < 0.02 else width
            exactHeight = height

            dprVerified = d.get('dprVerified', True)
            isZoomed = d.get('isZoomed', False)

            logger.info(f"📍 FULL USER-AGENT: {user_agent}")
            logger.info(f"📊 PARAMS: W={width}, H={height}, DPR={dpr}, RAM={ram}, Hz={refresh_rate}, GPU={gpu[:50]}")

            ua_id = parse_device_from_ua(user_agent)
            logger.info(f"📍 PARSED UA_ID: {ua_id}")

            detection_log = {
                "ua_detected": ua_id,
                "ua_full": user_agent[:100] + "..." if len(user_agent) > 100 else user_agent,
                "fingerprint": f"{exactWidth}x{exactHeight} @ {dpr}x DPR, {refresh_rate}Hz, RAM: {ram}GB, Cores: {cores}, GPU: {gpu}",
                "canvas_hash": canvas_hash,
                "dpr": dpr,
                "dprVerified": dprVerified,
                "isZoomed": isZoomed,
                "ram": ram,
                "cores": cores
            }

            # Priorytet 1: User-Agent z dokładnym dopasowaniem
            if ua_id:
                model_name = EXTERNAL_DB.get(ua_id) or STATIC_IDENTIFIERS.get(ua_id) or ANDROID_IDENTIFIERS.get(ua_id)
                if model_name:
                    logger.info(f"✅ Device identified via UA_EXACT: {model_name}")
                    accessory_codes = ACCESSORY_CODES.get(model_name, {"screen": "N/A", "case": "N/A"})
                    detection_log["method"] = "UA_EXACT"
                    detection_log["matched_id"] = ua_id

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

                # UA wykryty ale nie ma w bazie
                logger.info(f"✅ Device identified via UA_RAW: {ua_id}")
                detection_log["method"] = "UA_RAW"
                detection_log["matched_id"] = ua_id

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

            # Priorytet 3: Baza AI (fingerprint)
            dpr_rounded = round(float(dpr), 2)
            signature = f"{exactWidth}_{exactHeight}_{dpr_rounded}_{ram}_{refresh_rate}_{gpu}_{canvas_hash}"

            if signature in BRAIN:
                models = BRAIN[signature]
                top_model = max(models, key=models.get)
                total_count = sum(models.values())
                confidence = int((models[top_model] / total_count) * 100)
                logger.info(f"✅ Device identified via AI: {top_model} ({confidence}% confidence)")
                accessory_codes = ACCESSORY_CODES.get(top_model, {"screen": "N/A", "case": "N/A"})
                detection_log["method"] = "AI_FINGERPRINT"
                detection_log["signature"] = signature
                detection_log["ai_models"] = dict(models)

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

            # Priorytet 4: Heurystyka
            suggestions = find_top_3_matches(
                exactWidth,
                exactHeight,
                refresh_rate,
                gpu,
                dpr,
                ram,
                cores,
                user_agent=user_agent
            )

            if suggestions:
                detection_log["method"] = "HEURISTIC_TOP3"
                detection_log["suggestions"] = suggestions

                # Automatyczna decyzja jeśli top >= 90% i second < 60%
                if len(suggestions) >= 1:
                    top_confidence = suggestions[0]["confidence"]
                    second_confidence = suggestions[1]["confidence"] if len(suggestions) >= 2 else 0

                    if top_confidence >= 90 and second_confidence < 60:
                        model_name = suggestions[0]["model"]
                        clean_model_name = model_name.replace(" (symulacja?)", "")
                        accessory_codes = ACCESSORY_CODES.get(clean_model_name, {"screen": "N/A", "case": "N/A"})

                        logger.info(f"✅ AUTO-DECISION: {model_name} ({top_confidence}% vs {second_confidence}%)")

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

                # Brak automatycznej decyzji - pokaż sugestie
                logger.info(f"Device not found - suggesting top 3 matches")

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

            # Walidacja
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
            if not isinstance(model, str) or len(model) > 100:
                return jsonify({"error": "Invalid model value"}), 400
            if not isinstance(dpr, (int, float)) or dpr <= 0 or dpr > 10:
                return jsonify({"error": "Invalid DPR value"}), 400
            if not isinstance(ram, (int, float)) or ram < -1 or ram > 100:
                return jsonify({"error": "Invalid RAM value"}), 400
            if not isinstance(cores, (int, float)) or cores < -1 or cores > 100:
                return jsonify({"error": "Invalid cores value"}), 400

            # NORMALIZACJA VIEWPORT
            exactWidth = round(width) if abs(width - round(width)) < 0.02 else width
            exactHeight = height

            dpr_rounded = round(float(dpr), 2)
            signature = f"{exactWidth}_{exactHeight}_{dpr_rounded}_{ram}_{refresh_rate}_{gpu}_{canvas_hash}"

            # Pobierz aktualną sygnaturę z BRAIN (może być zaktualizowana przez inny worker)
            if signature not in BRAIN:
                BRAIN[signature] = {}

            if model not in BRAIN[signature]:
                BRAIN[signature][model] = 0

            BRAIN[signature][model] += 1

            # Limit liczby modeli per sygnatura
            if len(BRAIN[signature]) > MAX_MODELS_PER_SIGNATURE:
                min_model = min(BRAIN[signature], key=BRAIN[signature].get)
                del BRAIN[signature][min_model]

            # Limit całkowitej liczby sygnatur
            if len(BRAIN) > MAX_BRAIN_SIGNATURES:
                oldest_sig = next(iter(BRAIN))
                del BRAIN[oldest_sig]

            # ✅ ATOMICZNY ZAPIS - bezpieczny dla wielu workerów
            # Zamiast save_brain() (nadpisuje cały BRAIN), używamy save_brain_signature()
            # która atomicznie zapisuje tylko tę jedną sygnaturę
            model_data = BRAIN[signature]
            success = save_brain_signature(signature, model_data)

            if not success:
                logger.error(f"❌ Failed to save brain signature: {signature[:50]}...")
                return jsonify({"error": "Failed to save brain signature"}), 500

            logger.info(f"✅ Brain learned: {model} for signature {signature[:50]}... (count: {BRAIN[signature][model]})")

            return jsonify({
                "success": True,
                "message": f"Brain learned: {model}",
                "signature": signature,
                "count": BRAIN[signature][model],
                "total_signatures": len(BRAIN)
            })

        except Exception as e:
            logger.error(f"Error in learn: {e}", exc_info=True)
            return jsonify({"error": "Internal server error"}), 500
