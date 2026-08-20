"""
Unit and property tests for AuthController — POST /auth/login.

Test layout
-----------
* post_login()         — shared helper used by all tests in this module
* Property 8           — JWT identity is always str(user.id)          [task 6.2]
* Property 9           — Success response fields / no sensitive data   [task 6.3]
* Property 10          — No HTTP 500 for any JSON-parseable input      [task 6.4]
* Example-based tests  — concrete login scenarios                      [task 7.1]
* Error handler test   — global 500 handler returns structured JSON    [task 9.2]
"""

import pytest
import unittest.mock as mock
from hypothesis import given, settings, strategies as st


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def post_login(client, payload):
    """POST /auth/login with a JSON payload. Returns a Flask test Response."""
    return client.post("/auth/login", json=payload)


# ---------------------------------------------------------------------------
# Helper: build a simple namespace object that looks like a User,
# without any SQLAlchemy instrumentation.
# ---------------------------------------------------------------------------

def _make_user(id=1, username="testuser", email="test@example.com", password_hash=""):
    """Return a lightweight user-like object with no SQLAlchemy involvement."""
    user = mock.MagicMock(spec=["id", "username", "email", "password_hash"])
    user.id = id
    user.username = username
    user.email = email
    user.password_hash = password_hash
    return user


# ---------------------------------------------------------------------------
# Property 8 — JWT identity is always str(user.id)
# Feature: user-login, Property 8: JWT identity is always str(user.id)
# Validates: Requirements 5.1
# ---------------------------------------------------------------------------

@given(user_id=st.integers(min_value=1, max_value=10**9))
@settings(max_examples=100)
def test_jwt_identity_is_str_user_id(client, user_id):
    """**Validates: Requirements 5.1**

    For any user with an integer id, the controller must call
    create_access_token(identity=str(user.id)).
    """
    user = _make_user(id=user_id, email=f"u{user_id}@example.com")
    captured = {}

    def fake_create_access_token(identity):
        captured["identity"] = identity
        return "fake.jwt.token"

    with mock.patch("controllers.auth_controller._service.login", return_value=user), \
         mock.patch("controllers.auth_controller.create_access_token",
                    side_effect=fake_create_access_token):
        response = post_login(client, {"email": user.email, "password": "any"})

    assert response.status_code == 200
    assert captured.get("identity") == str(user_id)


# ---------------------------------------------------------------------------
# Property 9 — Success response contains required fields and no sensitive fields
# Feature: user-login, Property 9: success response contains required fields and no sensitive fields
# Validates: Requirements 5.3, 5.4, 7.2
# ---------------------------------------------------------------------------

@given(
    user_id=st.integers(min_value=1, max_value=10**9),
    username=st.text(min_size=3, max_size=30).map(str.strip).filter(lambda s: len(s) >= 3),
    email=st.from_regex(r"[^@\s]+@[^@\s]+\.[^@\s]+", fullmatch=True),
)
@settings(max_examples=100)
def test_success_response_fields_and_no_sensitive_data(client, user_id, username, email):
    """**Validates: Requirements 5.3, 5.4, 7.2**

    The 200 response must contain message, id, username, email, access_token,
    and must NOT contain password or password_hash.
    """
    user = _make_user(id=user_id, username=username, email=email)

    with mock.patch("controllers.auth_controller._service.login", return_value=user), \
         mock.patch("controllers.auth_controller.create_access_token",
                    return_value="fake.token"):
        response = post_login(client, {"email": email, "password": "any"})

    assert response.status_code == 200
    body = response.get_json()
    # Required fields
    assert "message" in body
    assert body["id"] == user_id
    assert body["username"] == username
    assert body["email"] == email
    assert body["access_token"] == "fake.token"
    # Sensitive fields must not appear
    assert "password" not in body
    assert "password_hash" not in body


# ---------------------------------------------------------------------------
# Property 10 — No HTTP 500 for any JSON-parseable input
# Feature: user-login, Property 10: no HTTP 500 for any JSON-parseable input
# Validates: Requirements 6.3
# ---------------------------------------------------------------------------

@given(
    payload=st.dictionaries(
        keys=st.text(max_size=20),
        values=st.one_of(st.text(), st.integers(), st.none(), st.booleans()),
        max_size=5,
    )
)
@settings(max_examples=200)
def test_no_500_for_any_json_input(client, payload):
    """**Validates: Requirements 6.3**

    For any JSON-serialisable dict, POST /auth/login must never return 500.
    """
    response = post_login(client, payload)
    assert response.status_code != 500


# ---------------------------------------------------------------------------
# Example-based tests — concrete login scenarios
# Validates: Requirements 1.2, 1.3, 2.1, 3.3, 4.3, 5.1, 5.3, 5.4, 6.1
# ---------------------------------------------------------------------------

def test_login_email_correct_password_returns_200(client, seeded_login_user):
    """Valid email + correct password → 200 with all required fields, no password_hash."""
    user, password = seeded_login_user
    response = post_login(client, {"email": user.email, "password": password})
    assert response.status_code == 200
    body = response.get_json()
    assert body["id"] == user.id
    assert body["username"] == user.username
    assert body["email"] == user.email
    assert "access_token" in body
    assert "message" in body
    assert "password_hash" not in body
    assert "password" not in body


def test_login_username_correct_password_returns_200(client, seeded_login_user):
    """Valid username + correct password → 200, username in response matches."""
    user, password = seeded_login_user
    response = post_login(client, {"username": user.username, "password": password})
    assert response.status_code == 200
    body = response.get_json()
    assert body["username"] == user.username


def test_login_wrong_password_returns_401(client, seeded_login_user):
    """Correct email but wrong password → 401 with 'Credenciales incorrectas.'."""
    user, _ = seeded_login_user
    response = post_login(client, {"email": user.email, "password": "wrongpassword"})
    assert response.status_code == 401
    body = response.get_json()
    assert body["error"] == "Credenciales incorrectas."


def test_login_nonexistent_email_returns_401(client, seeded_login_user):
    """Non-existent email → 401 with the same uniform error message."""
    _, password = seeded_login_user
    response = post_login(client, {"email": "nobody@nowhere.com", "password": password})
    assert response.status_code == 401
    body = response.get_json()
    assert body["error"] == "Credenciales incorrectas."


def test_login_empty_body_returns_400(client):
    """Empty JSON body {} → 400 (no identifier provided)."""
    response = post_login(client, {})
    assert response.status_code == 400


def test_login_non_json_body_returns_400(client):
    """Non-JSON body (text/plain) → 400."""
    response = client.post(
        "/auth/login",
        data="not json",
        content_type="text/plain",
    )
    assert response.status_code == 400


def test_create_access_token_called_with_str_user_id(client, seeded_login_user):
    """create_access_token must be called with identity=str(user.id)."""
    user, password = seeded_login_user
    with mock.patch(
        "controllers.auth_controller.create_access_token",
        wraps=lambda identity: f"token_for_{identity}",
    ) as mock_token:
        response = post_login(client, {"email": user.email, "password": password})
    assert response.status_code == 200
    mock_token.assert_called_once_with(identity=str(user.id))


# ---------------------------------------------------------------------------
# Global error handler test
# Feature: unexpected repository exception → 500 with structured JSON
# Validates: Requirements 6.3
# ---------------------------------------------------------------------------

def test_global_error_handler_returns_structured_json(client):
    """Unexpected Exception in repository → 500 with {"error": "Error interno del servidor."}."""
    with mock.patch(
        "repositories.user_repository.UserRepository.find_by_email",
        side_effect=Exception("db error"),
    ):
        response = post_login(client, {"email": "any@example.com", "password": "anypassword"})
    assert response.status_code == 500
    body = response.get_json()
    assert body == {"error": "Error interno del servidor."}
