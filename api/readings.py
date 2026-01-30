from flask import Blueprint, g, request, url_for, current_app
from werkzeug.security import check_password_hash
from typing import Optional

from .database import db_client

bp = Blueprint("readings", __name__)

def validate_payload(payload: dict, required_fields: list) -> Optional[dict]:
    if all(field in payload for field in required_fields):
        return payload
    
    return None

@bp.before_request
def validate_permissions():
    """Validacion de los permisos del dispositivo que intenta registrar datos"""
    device_id, ak = request.headers.get("X-API-KEY").split(".", 1)
    
    if not device_id or not ak:
        return {"error": "Credencial Invalida"}, 400

    g.device = db_client.access.fetch_device_by_id(id=device_id)
    if g.device is None or not check_password_hash(g.device["api_key"], ak):
        return {"error": "No autorizado o dispositivo inexistente"}, 401
    
@bp.post("/")
def record_reading():
    """Registra una nueva lectura de sensores"""
    if payload := validate_payload(request.json, ["temp", "humidity", "pm10", "gas"]):
        payload["device_id"] = g.device["id"]
        g.db_access.record_reading(payload)
    
        return {"message": "Ok!"}, 201

    return {"error": "Faltan campos obligatorios"}, 400
