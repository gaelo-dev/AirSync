from flask import Blueprint, g, request, current_app
from werkzeug.security import generate_password_hash
import secrets

from .database import pool, DeviceId
from .errors import ForbiddenError, NotFoundError
from .utils import validate_fields

bp = Blueprint("admin", __name__)

@bp.before_request
def validate_permissions():
    """Validacion de los permisos de admin"""
    admin_key = request.headers.get("Admin-Authorization")
    if admin_key != current_app.config["ADMIN_TOKEN"]:
        raise ForbiddenError()

@bp.route("/")
def index():
    return "Hello, Admin!"

@bp.post("/devices")
@validate_fields(["name"])
def create_device(payload: dict):
    device_name = payload["name"]
    raw_api_key = secrets.token_hex(24) 
    
    # Guardamos solo el HASH en la base de datos para mayor seguridad
    hashed_key = generate_password_hash(raw_api_key)
    device = pool.session.create_device({
        "name": device_name,
        "api_key": hashed_key,
    })
    
    device["api_key"] = f"{device['id']}.{raw_api_key}"
    return (device, 201)

@bp.get("/devices/<int:device_id>")
def get_device(device_id: DeviceId = None):
    if device_id is None:
        return [
            { k: v for k, v in device.items() if k != "api_key" }
            for device in pool.session.fetch_devices()
        ]
    
    device = pool.session.fetch_device_by_id(id=device_id) 
    if device is None:
        raise NotFoundError(
            message = f"Dispositivo (ID: {device_id}) no encontrado"
        )
    
    device.pop("api_key")
    return device

@bp.patch("/devices/<int:device_id>")
@validate_fields(["new_name"])
def patch_device(payload: dict, device_id: DeviceId):
    device = pool.session.update_device_name(id=device_id, name=payload["new_name"])

    if device is None:
        raise NotFoundError(
            message = f"Dispositivo (ID: {device_id}) no encontrado"
        )
    
    device.pop("api_key")
    return device

@bp.delete("/devices/<int:device_id>")
def delete_device(device_id: DeviceId):
    pool.session.delete_device(id=device_id)
    return "", 204
