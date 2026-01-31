"""
SHARK v18 - Models Package
Zawiera wszystkie dane modelowe (HEURISTIC_DB, identyfikatory, kody akcesoriów)
"""
from app.models.heuristic_db import HEURISTIC_DB
from app.models.identifiers import STATIC_IDENTIFIERS, ANDROID_IDENTIFIERS, ACCESSORY_CODES

__all__ = [
    'HEURISTIC_DB',
    'STATIC_IDENTIFIERS',
    'ANDROID_IDENTIFIERS',
    'ACCESSORY_CODES'
]
