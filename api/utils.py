import functools 
from errors import BadRequestError
from flask import request

def validate_fields(required_fields: list):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            payload = request.get_json(silent=True) or {}
            
            # Buscamos los campos que faltan o están vacíos
            missing = [field for field in required_fields if not payload.get(field)]
            if missing:
                raise BadRequestError(
                    message = "Campos obligatorios faltantes",
                    payload = {"missing_fields": missing}
                )
            
            # Si todo está bien, pasamos el JSON a la función como un argumento
            return f(payload, *args, **kwargs)
        
        return decorated_function

    return decorator
