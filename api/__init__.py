from flask import Flask
from datetime import datetime, UTC
import json
import os

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_file(
       os.path.join(app.instance_path, "config.json"),
       load=json.load
    )
    
    @app.route("/")
    def index():
        return "Hello, World!"

    @app.route("/ping")
    def ping():
        now = datetime.now(UTC)
        return {
            "status": "OK",
            "message": "pong!",
            "timestamp": now.isoformat().replace("+00:00", "Z")
        }

    # Configurando la conexion a la base de datos
    from . import database
    database.init_app(app)

    # Registrando los blueprints en la app
    from . import admin
    from . import readings
    from . import errors

    app.register_blueprint(admin.bp, url_prefix="/admin")    
    app.register_blueprint(readings.bp, url_prefix="/readings")
    app.register_blueprint(errors.bp)

    return app
