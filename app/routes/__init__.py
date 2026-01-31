"""
SHARK v18 - Routes Package
Zawiera wszystkie endpointy API
"""
from app.routes.api_routes import register_api_routes
from app.routes.admin_routes import register_admin_routes

def register_all_routes(app, limiter):
    """Rejestruje wszystkie route'y w aplikacji Flask"""
    register_api_routes(app, limiter)
    register_admin_routes(app)

__all__ = ['register_all_routes']
