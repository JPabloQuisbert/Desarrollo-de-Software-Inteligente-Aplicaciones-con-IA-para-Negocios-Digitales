import os
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from extensions import db, migrate, jwt
from config import config_by_name


def create_app(config_name: str = None):
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Registrar blueprints
    from modules.auth.controller import auth_bp
    app.register_blueprint(auth_bp)

    @app.route("/")
    def home():
        return "Hola Flask"

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return e
        return jsonify({"error": "Error interno del servidor."}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
