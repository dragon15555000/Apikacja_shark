"""
SHARK v18 - Admin Routes
Endpointy panelu administracyjnego
"""
from flask import request, jsonify, render_template
from datetime import datetime
from app.config import USE_MONGODB, BRAIN, logger
from app.database import (
    verified_models_collection, detection_logs_collection, brain_collection,
    external_db_collection, get_verified_models, add_verified_model,
    update_verified_model, delete_verified_model, get_detection_logs,
    clear_detection_logs, save_brain
)

def register_admin_routes(app):
    """Rejestruje endpointy panelu administracyjnego"""

    @app.route('/admin')
    def admin_panel():
        """Admin panel - HTML page"""
        if USE_MONGODB:
            return render_template('admin.html')
        return jsonify({"error": "Admin panel requires MongoDB"}), 503

    @app.route('/admin/api/brain')
    def admin_get_brain():
        """Get brain statistics"""
        try:
            total_signatures = len(BRAIN)
            total_models = sum(len(models) for models in BRAIN.values())
            top_signatures = sorted(
                [(sig[:50], sum(models.values()), dict(models)) for sig, models in BRAIN.items()],
                key=lambda x: x[1],
                reverse=True
            )[:20]

            return jsonify({
                "total_signatures": total_signatures,
                "total_models": total_models,
                "top_signatures": [{"signature": sig, "count": count, "models": models} for sig, count, models in top_signatures]
            })
        except Exception as e:
            logger.error(f"Error getting brain stats: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/admin/api/brain/clear', methods=['POST'])
    def admin_clear_brain():
        """Clear all brain data"""
        try:
            BRAIN.clear()
            save_brain()
            logger.info("🗑️ Brain cleared by admin")
            return jsonify({"success": True, "message": "Brain cleared successfully"})
        except Exception as e:
            logger.error(f"Error clearing brain: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/admin/api/verified-models', methods=['GET'])
    def admin_get_verified_models():
        """Get all verified models"""
        try:
            models = get_verified_models()
            return jsonify({"models": models, "count": len(models)})
        except Exception as e:
            logger.error(f"Error getting verified models: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/admin/api/verified-models', methods=['POST'])
    def admin_add_verified_model():
        """Add new verified model"""
        try:
            data = request.json
            required_fields = ['system_name', 'w', 'h', 'dpr', 'hz', 'gpu']
            missing = [f for f in required_fields if f not in data]
            if missing:
                return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

            model_data = {
                "system_name": data['system_name'],
                "w": data['w'],
                "h": data['h'],
                "dpr": data['dpr'],
                "ram": data.get('ram', -1),
                "hz": data['hz'],
                "gpu": data['gpu'],
                "created_at": datetime.utcnow()
            }

            if add_verified_model(model_data):
                return jsonify({"success": True, "message": "Model added successfully"})
            else:
                return jsonify({"error": "Failed to add model"}), 500
        except Exception as e:
            logger.error(f"Error adding verified model: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/admin/api/verified-models/<system_name>', methods=['PUT'])
    def admin_update_verified_model(system_name):
        """Update verified model"""
        try:
            data = request.json
            if update_verified_model(system_name, data):
                return jsonify({"success": True, "message": "Model updated successfully"})
            else:
                return jsonify({"error": "Model not found or update failed"}), 404
        except Exception as e:
            logger.error(f"Error updating verified model: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/admin/api/verified-models/<system_name>', methods=['DELETE'])
    def admin_delete_verified_model(system_name):
        """Delete verified model"""
        try:
            if delete_verified_model(system_name):
                return jsonify({"success": True, "message": "Model deleted successfully"})
            else:
                return jsonify({"error": "Model not found"}), 404
        except Exception as e:
            logger.error(f"Error deleting verified model: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/admin/api/detection-logs', methods=['GET'])
    def admin_get_detection_logs():
        """Get detection logs"""
        try:
            limit = int(request.args.get('limit', 100))
            logs = get_detection_logs(limit)
            return jsonify({"logs": logs, "count": len(logs)})
        except Exception as e:
            logger.error(f"Error getting detection logs: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/admin/api/detection-logs/clear', methods=['POST'])
    def admin_clear_detection_logs():
        """Clear all detection logs"""
        try:
            count = clear_detection_logs()
            return jsonify({"success": True, "message": f"Cleared {count} logs"})
        except Exception as e:
            logger.error(f"Error clearing detection logs: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/admin/api/models/import-matomo', methods=['POST'])
    def admin_import_matomo_models():
        """Import models from Matomo database"""
        try:
            if not USE_MONGODB:
                return jsonify({"error": "MongoDB required for this operation"}), 503

            # Ta funkcjonalność wymaga setup_database.py
            return jsonify({
                "message": "Please run 'python setup_database.py' to import Matomo models",
                "info": "This operation is performed via CLI for safety"
            })
        except Exception as e:
            logger.error(f"Error in import-matomo: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/admin/api/models/export')
    def admin_export_models():
        """Export all models to JSON"""
        try:
            models = get_verified_models()
            return jsonify({
                "models": models,
                "count": len(models),
                "exported_at": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Error exporting models: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/admin/api/sync-to-mongodb', methods=['POST'])
    def admin_sync_to_mongodb():
        """Sync all data to MongoDB"""
        try:
            if not USE_MONGODB:
                return jsonify({"error": "MongoDB not configured"}), 503

            # Sync BRAIN
            save_brain()

            return jsonify({
                "success": True,
                "message": "Data synced to MongoDB successfully",
                "brain_signatures": len(BRAIN)
            })
        except Exception as e:
            logger.error(f"Error syncing to MongoDB: {e}")
            return jsonify({"error": str(e)}), 500
