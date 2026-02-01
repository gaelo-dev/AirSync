from flask import Blueprint
from werkzeug.exceptions import HTTPException

class APIError(Exception):
    """Clase base para los errores de la API"""
    status_code = 500
    message = "Error Interno"
    
    def __init__(self, *, message=None, payload=None):
        super().__init__()
        if message is not None:
            self.message = message
        
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["error"] = self.message
        return rv
    
class BadRequestError(APIError):
    status_code = 400
    message = "La solicitud contiene parámetros inválidos"

class UnauthorizedError(APIError):
    status_code = 401
    message = "Se requiere autenticación para acceder"    

class ForbiddenError(APIError):
    status_code = 403
    message = "No tienes permisos para realizar esta acción"

bp = Blueprint('errors', __name__)

@bp.app_errorhandler(APIError)
def handle_api_error(e):
    return e.to_dict(), e.status_code
