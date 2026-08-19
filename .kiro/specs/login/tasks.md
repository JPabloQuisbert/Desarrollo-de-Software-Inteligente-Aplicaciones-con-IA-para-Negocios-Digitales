# Tasks — User Login

## Overview

Implementation tasks derived from the [requirements](requirements.md) and [design](design.md) for the login feature. The schema and service layers are already complete; the remaining work is JWT integration and wiring it into the controller and app factory.

---

- [x] 1. Install and pin `flask-jwt-extended`
  - Add `flask-jwt-extended==4.7.1` to `requirements.txt` (create the file if it does not exist).
  - Install the package in the active virtual environment: `pip install flask-jwt-extended==4.7.1`.
  - **Acceptance:** `pip show flask-jwt-extended` confirms the package is installed at version 4.7.1.
  - **Files:** `requirements.txt`

- [x] 2. Add `JWTManager` to `extensions.py`
  - Import `JWTManager` from `flask_jwt_extended`.
  - Create a module-level `jwt = JWTManager()` instance alongside the existing `db` and `migrate` instances.
  - **Acceptance:** `extensions.py` exports `jwt` and the module imports without errors.
  - **Files:** `extensions.py`

- [x] 3. Add `JWT_SECRET_KEY` to `config.py`
  - In the base `Config` class, add `JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")`.
  - Optionally add `JWT_ACCESS_TOKEN_EXPIRES` (e.g., `timedelta(hours=1)`) to limit token lifetime.
  - **Acceptance:** `Config().JWT_SECRET_KEY` returns the env-var value when set, and a fallback otherwise.
  - **Files:** `config.py`

- [x] 4. Initialize `JWTManager` in the app factory (`app.py`)
  - Import `jwt` from `extensions`.
  - Call `jwt.init_app(app)` after `db.init_app(app)` and `migrate.init_app(app, db)`.
  - **Acceptance:** `create_app()` runs without errors and `app.extensions` includes the JWT manager.
  - **Files:** `app.py`

- [x] 5. Update `auth_controller.py` to return a JWT on successful login
  - Import `create_access_token` from `flask_jwt_extended`.
  - Split the existing single `try/except` in the `login` view into two blocks: one for validation errors (→ HTTP 400) and one for authentication errors (→ HTTP 401).
  - After a successful `_service.login()` call, generate `access_token = create_access_token(identity=str(user.id))`.
  - Return HTTP 200 with `{ "message", "id", "username", "email", "access_token" }`. Do **not** include `password_hash`.
  - **Acceptance:** `POST /auth/login` with valid credentials returns HTTP 200 and an `access_token` field; invalid credentials return HTTP 401; malformed input returns HTTP 400.
  - **Files:** `controllers/auth_controller.py`

- [x] 6. Smoke-test the full login flow
  - Start the app and send test requests with `curl` or a REST client.
  - Verify the three main scenarios from the API contract:
    - Login with email + correct password → HTTP 200 + `access_token`.
    - Login with username + correct password → HTTP 200 + `access_token`.
    - Login with wrong password → HTTP 401, `"Credenciales incorrectas."`.
    - Login with no identifier → HTTP 400.
  - Confirm `password_hash` is absent from all responses.
  - **Files:** none (verification only)
