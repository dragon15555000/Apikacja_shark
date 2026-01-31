"""
SHARK v18 - Validators Module
Dekoratory i funkcje walidacyjne
"""
from functools import wraps
from flask import request, jsonify

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
