from flask import Blueprint, g, request
from werkzeug.security import check_password_hash

from .database import db_client, ReadingCreate
from .errors import UnauthorizedError
from .utils import validate_fields

bp = Blueprint("readings", __name__)

@bp.before_request
def authentication():
    """Autenticación del dispositivo que intenta registrar datos"""
    device_id, ak = request.headers.get("X-API-KEY").split(".", 1)
    
    if not device_id or not ak:
        raise UnauthorizedError(
            message = "Credencial Invalida",
            payload = {"code": "INVALID_TOKEN_FORMAT"}
        )

    g.device = db_client.access.fetch_device_by_id(id=device_id)
    if g.device is None or not check_password_hash(g.device["api_key"], ak):
        raise UnauthorizedError()

@bp.post("/")
@validate_fields(["temp", "humidity", "pm10", "gas"])
def record_reading(payload: ReadingCreate):
    """Registra una nueva lectura de sensores"""
    payload["device_id"] = g.device["id"]
    g.db_access.record_reading(payload)

    return {"message": "Ok!"}, 201
