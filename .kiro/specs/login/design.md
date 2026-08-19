# Design — User Login

## Overview

This document describes the technical architecture for the `/auth/login` endpoint of the Flask REST API. The feature allows registered users to authenticate using either their **email** or **username** along with their password. On success, the server returns the user's public data and a **JWT access token** generated with `flask-jwt-extended`.

---

## Architecture

### Component Diagram

```
HTTP Client
    │
    ▼
┌─────────────────────────────┐
│  Controller (Flask Blueprint)│  controllers/auth_controller.py
│  POST /auth/login            │
└──────────────┬──────────────┘
               │ LoginInput (dataclass)
               ▼
┌─────────────────────────────┐
│  Validator                   │  schemas/user_schema.py
│  UserValidator.validate_login│
└──────────────┬──────────────┘
               │ LoginInput
               ▼
┌─────────────────────────────┐
│  Service                     │  services/auth_service.py
│  AuthService.login           │
└──────────────┬──────────────┘
               │ email | username
               ▼
┌─────────────────────────────┐
│  Repository                  │  repositories/user_repository.py
│  find_by_email / find_by_    │
│  username                    │
└──────────────┬──────────────┘
               │ User | None
               ▼
┌─────────────────────────────┐
│  Model                       │  models/user.py
│  User (SQLAlchemy)           │
└─────────────────────────────┘
```

### Data Flow

1. Client sends `POST /auth/login` with a JSON body containing `email` or `username`, and `password`.
2. The controller calls `UserValidator.validate_login()` to sanitize and validate the input, returning a `LoginInput` dataclass. Raises `ValueError` (→ HTTP 400) on invalid input.
3. The controller passes `LoginInput` to `AuthService.login()`.
4. The service resolves the user via `UserRepository.find_by_email()` or `find_by_username()` depending on which identifier was provided.
5. If no user is found, or `check_password_hash` fails, a generic `ValueError` is raised (→ HTTP 401).
6. On success, the service returns the `User` model instance.
7. The controller calls `create_access_token(identity=user.id)` from `flask-jwt-extended` to generate a JWT.
8. The controller returns HTTP 200 with `id`, `username`, `email`, and `access_token`. The `password_hash` is never included in the response.

---

## Components

### UserValidator
**File:** `schemas/user_schema.py`  
**Responsibility:** Validate and sanitize raw request data. Return typed dataclasses.  
**Changes required:** None. `validate_login` already supports both `email` and `username` as identifiers and enforces `password` presence.

---

### LoginInput
**File:** `schemas/user_schema.py`  
**Responsibility:** Typed container for validated login input.  
**Changes required:** None. Already defined as:
```python
@dataclass
class LoginInput:
    password: str
    email: str | None = None
    username: str | None = None
```

---

### AuthService
**File:** `services/auth_service.py`  
**Responsibility:** Business logic — resolve the user by identifier and verify the password hash.  
**Changes required:** None. `login()` already branches on `input_data.email` vs `input_data.username` and calls `check_password_hash`. Token generation is **not** the service's responsibility; it belongs in the controller layer.

---

### UserRepository
**File:** `repositories/user_repository.py`  
**Responsibility:** Data access — query the database for a user record.  
**Changes required:** None. `find_by_email` and `find_by_username` are already implemented.

---

### User (Model)
**File:** `models/user.py`  
**Responsibility:** SQLAlchemy ORM model for the `users` table.  
**Changes required:** None. Fields `id`, `username`, `email`, and `password_hash` satisfy all requirements.

---

### AuthController
**File:** `controllers/auth_controller.py`  
**Responsibility:** Handle HTTP request/response cycle. Delegate validation and business logic. Generate JWT on successful login.  
**Changes required:**
- Import `create_access_token` from `flask_jwt_extended`.
- After a successful `_service.login()` call, generate a JWT token: `create_access_token(identity=str(user.id))`.
- Include `access_token` in the success response body alongside `id`, `username`, and `email`.
- Do **not** include `password_hash` in any response.
- Validation errors (`ValueError` from the validator) must return HTTP **400**; authentication errors (`ValueError` from the service) must return HTTP **401**.

Example updated `login` handler:
```python
from flask_jwt_extended import create_access_token

@auth_bp.route("/login", methods=["POST"])
def login():
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
```

---

### Application Factory
**File:** `app.py`  
**Responsibility:** Create and configure the Flask app, register extensions and blueprints.  
**Changes required:**
- Import `JWTManager` from `flask_jwt_extended`.
- Set `JWT_SECRET_KEY` in the app config (loaded from environment variable `JWT_SECRET_KEY`; never hardcoded).
- Call `jwt.init_app(app)` after `db.init_app(app)`.

---

### Config
**File:** `config.py`  
**Responsibility:** Environment-based configuration.  
**Changes required:**
- Add `JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")` to the base `Config` class.
- In production, `JWT_SECRET_KEY` must be set as a real secret via environment variable.

---

### Extensions
**File:** `extensions.py`  
**Responsibility:** Hold shared extension instances.  
**Changes required:**
- Add `from flask_jwt_extended import JWTManager` and `jwt = JWTManager()`.

---

## API Contract

### POST /auth/login

**Request body (JSON):**

Login with email:
```json
{
  "email": "user@example.com",
  "password": "secret123"
}
```

Login with username:
```json
{
  "username": "johndoe",
  "password": "secret123"
}
```

---

**Responses:**

| Status | Condition | Body |
|--------|-----------|------|
| `200 OK` | Valid credentials | `{ "message": "Login exitoso.", "id": 1, "username": "johndoe", "email": "user@example.com", "access_token": "<jwt>" }` |
| `400 Bad Request` | Missing/invalid `email` format | `{ "error": "El correo electrónico no es válido." }` |
| `400 Bad Request` | Neither `email` nor `username` provided | `{ "error": "Debes proporcionar un correo electrónico o nombre de usuario." }` |
| `400 Bad Request` | Missing `password` | `{ "error": "La contraseña es requerida." }` |
| `400 Bad Request` | Empty or non-JSON body | `{ "error": "..." }` |
| `401 Unauthorized` | Wrong password or unknown identifier | `{ "error": "Credenciales incorrectas." }` |

---

## Security Considerations

- **Generic error message:** Both "user not found" and "wrong password" return the same `"Credenciales incorrectas."` message and HTTP 401, to prevent user enumeration.
- **Password hashing:** Passwords are never stored or returned in plain text. `werkzeug.security.check_password_hash` is used for verification.
- **No password in response:** The `password_hash` field is never serialized in any API response.
- **JWT secret:** `JWT_SECRET_KEY` must be a long, random, unpredictable string in production and must be injected via environment variable — never committed to source control.
- **Token expiry:** Configure `JWT_ACCESS_TOKEN_EXPIRES` in `Config` (e.g., `timedelta(hours=1)`) to limit the lifetime of issued tokens.
- **HTTPS:** All login traffic must be served over HTTPS in production to protect credentials and tokens in transit.

---

## Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| `flask-jwt-extended` | JWT generation and validation | `pip install flask-jwt-extended` |
| `flask-sqlalchemy` | ORM and database access | already installed |
| `flask-migrate` | Database migrations | already installed |
| `werkzeug` | Password hashing (`generate_password_hash`, `check_password_hash`) | already installed (Flask dependency) |

Add `flask-jwt-extended` to `requirements.txt`:
```
flask-jwt-extended==4.7.1
```
