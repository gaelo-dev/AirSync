from flask import Blueprint, g, request, current_app
from werkzeug.security import generate_password_hash
import secrets

from .database import db_client, DeviceId
from .errors import ForbiddenError
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
def create_device(payload):
    device_name = payload.get("name")
    raw_api_key = secrets.token_hex(24) 
    
    # Guardamos solo el HASH en la base de datos para mayor seguridad
    hashed_key = generate_password_hash(raw_api_key)
    device = db_client.access.create_device({
        "name": device_name,
        "api_key": hashed_key,
    })
    
    device["api_key"] = f"{device['id']}.{raw_api_key}"
    return (device, 201)
