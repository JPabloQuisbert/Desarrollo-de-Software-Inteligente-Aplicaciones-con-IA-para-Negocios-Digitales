from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token

from schemas.user_schema import UserValidator
from repositories.user_repository import UserRepository
from services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

_validator = UserValidator()
_service = AuthService(UserRepository())


@auth_bp.route("/register", methods=["POST"])
def register():
    """Registra un nuevo usuario."""
    try:
        input_data = _validator.validate_register(request.get_json(silent=True) or {})
        user = _service.register(input_data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"message": "Usuario registrado.", "id": user.id, "username": user.username}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Autentica un usuario con email o username y contraseña, devuelve un JWT."""
    try:
        input_data = _validator.validate_login(request.get_json(silent=True) or {})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        user = _service.login(input_data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        "message": "Login exitoso.",
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "access_token": access_token,
    }), 200
