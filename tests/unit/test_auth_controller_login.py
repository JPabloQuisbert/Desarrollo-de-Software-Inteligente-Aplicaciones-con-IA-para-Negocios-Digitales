"""
Unit and property tests for AuthController — POST /auth/login.
"""

import pytest
import unittest.mock as mock
from hypothesis import given, settings, strategies as st


def post_login(client, payload):
    return client.post("/auth/login", json=payload)


def _make_user(id=1, username="testuser", email="test@example.com", password_hash=""):
    user = mock.MagicMock(spec=["id", "username", "email", "password_hash"])
    user.id = id
    user.username = username
    user.email = email
    user.password_hash = password_hash
    return user


# Feature: user-login, Property 8: JWT identity is always str(user.id)
@given(user_id=st.integers(min_value=1, max_value=10**9))
@settings(max_examples=100)
def test_jwt_identity_is_str_user_id(client, user_id):
    user = _make_user(id=user_id, email=f"u{user_id}@example.com")
    captured = {}

    def fake_token(identity):
        captured["identity"] = identity
        return "fake.jwt.token"

    with mock.patch("modules.auth.controller._service.login", return_value=user), \
         mock.patch("modules.auth.controller.create_access_token", side_effect=fake_token):
        response = post_login(client, {"email": user.email, "password": "any"})

    assert response.status_code == 200
    assert captured.get("identity") == str(user_id)


# Feature: user-login, Property 9: success response contains required fields and no sensitive fields
@given(
    user_id=st.integers(min_value=1, max_value=10**9),
    username=st.text(min_size=3, max_size=30).map(str.strip).filter(lambda s: len(s) >= 3),
    email=st.from_regex(r"[^@\s]+@[^@\s]+\.[^@\s]+", fullmatch=True),
)
@settings(max_examples=100)
def test_success_response_fields_and_no_sensitive_data(client, user_id, username, email):
    user = _make_user(id=user_id, username=username, email=email)

    with mock.patch("modules.auth.controller._service.login", return_value=user), \
         mock.patch("modules.auth.controller.create_access_token", return_value="fake.token"):
        response = post_login(client, {"email": email, "password": "any"})

    assert response.status_code == 200
    body = response.get_json()
    assert "message" in body
    assert body["id"] == user_id
    assert body["username"] == username
    assert body["email"] == email
    assert body["access_token"] == "fake.token"
    assert "password" not in body
    assert "password_hash" not in body


# Feature: user-login, Property 10: no HTTP 500 for any JSON-parseable input
@given(
    payload=st.dictionaries(
        keys=st.text(max_size=20),
        values=st.one_of(st.text(), st.integers(), st.none(), st.booleans()),
        max_size=5,
    )
)
@settings(max_examples=200)
def test_no_500_for_any_json_input(client, payload):
    response = post_login(client, payload)
    assert response.status_code != 500


# Example-based tests
def test_login_email_correct_password_returns_200(client, seeded_login_user):
    user, password = seeded_login_user
    response = post_login(client, {"email": user.email, "password": password})
    assert response.status_code == 200
    body = response.get_json()
    assert body["id"] == user.id
    assert body["username"] == user.username
    assert body["email"] == user.email
    assert "access_token" in body
    assert "password_hash" not in body


def test_login_username_correct_password_returns_200(client, seeded_login_user):
    user, password = seeded_login_user
    response = post_login(client, {"username": user.username, "password": password})
    assert response.status_code == 200
    assert response.get_json()["username"] == user.username


def test_login_wrong_password_returns_401(client, seeded_login_user):
    user, _ = seeded_login_user
    response = post_login(client, {"email": user.email, "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.get_json()["error"] == "Credenciales incorrectas."


def test_login_nonexistent_email_returns_401(client, seeded_login_user):
    _, password = seeded_login_user
    response = post_login(client, {"email": "nobody@nowhere.com", "password": password})
    assert response.status_code == 401
    assert response.get_json()["error"] == "Credenciales incorrectas."


def test_login_empty_body_returns_400(client):
    assert post_login(client, {}).status_code == 400


def test_login_non_json_body_returns_400(client):
    response = client.post("/auth/login", data="not json", content_type="text/plain")
    assert response.status_code == 400


def test_create_access_token_called_with_str_user_id(client, seeded_login_user):
    user, password = seeded_login_user
    with mock.patch(
        "modules.auth.controller.create_access_token",
        wraps=lambda identity: f"token_for_{identity}",
    ) as mock_token:
        response = post_login(client, {"email": user.email, "password": password})
    assert response.status_code == 200
    mock_token.assert_called_once_with(identity=str(user.id))


def test_global_error_handler_returns_structured_json(client):
    with mock.patch(
        "modules.auth.repository.UserRepository.find_by_email",
        side_effect=Exception("db error"),
    ):
        response = post_login(client, {"email": "any@example.com", "password": "anypassword"})
    assert response.status_code == 500
    assert response.get_json() == {"error": "Error interno del servidor."}
