"""
SHARK v18 - Utils Package
Funkcje pomocnicze i narzędzia
"""
from app.utils.logic import parse_device_from_ua, find_top_3_matches
from app.utils.validators import validate_json

__all__ = [
    'parse_device_from_ua',
    'find_top_3_matches',
    'validate_json'
]
