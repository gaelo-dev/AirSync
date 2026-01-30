from flask import Blueprint, g, request, url_for, current_app
from werkzeug.security import generate_password_hash
import secrets

from .database import db_client, DeviceId

bp = Blueprint("admin", __name__)

@bp.before_request
def validate_permissions():
    """Validacion de los permisos de admin, antes de realizar cualquier accion"""
    master_key = request.headers.get('Admin-Authorization')
    if master_key != current_app.config['ADMIN_TOKEN']:
        return {"error": "No autorizado"}, 401

@bp.route("/")
def index():
    return "Hello, Admin!"

@bp.post("/register-device")
def register_device():
    device_name = request.json.get('name')
    raw_api_key = secrets.token_hex(24) 
    
    # Guardamos solo el HASH en la base de datos para mayor seguridad
    hashed_key = generate_password_hash(raw_api_key)
    device = db_client.access.create_device({
        "name": device_name,
        "api_key": hashed_key,
    })
    
    device["api_key"] = f"{device['id']}.raw_api_key"
    return (device, 201)
