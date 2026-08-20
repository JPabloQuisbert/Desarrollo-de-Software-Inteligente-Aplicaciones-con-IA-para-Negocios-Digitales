"""
Property-based tests for AuthService.login — Properties 6 and 7.
"""

import pytest
from types import SimpleNamespace
from hypothesis import given, settings
from hypothesis import strategies as st
from werkzeug.security import generate_password_hash

from modules.auth.schema import LoginInput
from modules.auth.service import AuthService
from tests.unit.conftest import valid_email_st, valid_username_st, nonempty_password_st


def _make_user(id=1, username="testuser", email="test@example.com", password_hash=""):
    return SimpleNamespace(id=id, username=username, email=email, password_hash=password_hash)


class RepoNone:
    def find_by_email(self, email): return None
    def find_by_username(self, username): return None


class RepoWrongHash:
    def __init__(self, password):
        self._hash = generate_password_hash("different_" + password)
    def find_by_email(self, email):
        return _make_user(email=email, password_hash=self._hash)
    def find_by_username(self, username): return None


_KNOWN_PASSWORD = "correct_password"


class RepoByField:
    def __init__(self, active_field):
        if active_field not in ("email", "username"):
            raise ValueError("active_field must be 'email' or 'username'")
        self._active_field = active_field
        self._hash = generate_password_hash(_KNOWN_PASSWORD)
        self.called_methods = []

    def find_by_email(self, email):
        self.called_methods.append("find_by_email")
        if self._active_field == "email":
            return _make_user(email=email, password_hash=self._hash)
        return None

    def find_by_username(self, username):
        self.called_methods.append("find_by_username")
        if self._active_field == "username":
            return _make_user(username=username, password_hash=self._hash)
        return None


# Feature: user-login, Property 6: lookup is routed to the correct repository method
@given(email=valid_email_st, password=nonempty_password_st)
@settings(max_examples=100, deadline=None)
def test_email_lookup_routes_to_find_by_email(email, password):
    repo = RepoByField("email")
    service = AuthService(repo)
    try:
        service.login(LoginInput(email=email, username=None, password=password))
    except ValueError:
        pass
    assert "find_by_email" in repo.called_methods
    assert "find_by_username" not in repo.called_methods


@given(username=valid_username_st, password=nonempty_password_st)
@settings(max_examples=100, deadline=None)
def test_username_lookup_routes_to_find_by_username(username, password):
    repo = RepoByField("username")
    service = AuthService(repo)
    try:
        service.login(LoginInput(email=None, username=username, password=password))
    except ValueError:
        pass
    assert "find_by_username" in repo.called_methods
    assert "find_by_email" not in repo.called_methods


# Feature: user-login, Property 7: credential failure prevents account enumeration
@given(email=valid_email_st, password=nonempty_password_st)
@settings(max_examples=100, deadline=None)
def test_nonexistent_account_raises_uniform_message(email, password):
    service = AuthService(RepoNone())
    with pytest.raises(ValueError, match=r"^Credenciales incorrectas\.$"):
        service.login(LoginInput(email=email, username=None, password=password))


@given(email=valid_email_st, password=nonempty_password_st)
@settings(max_examples=100, deadline=None)
def test_wrong_password_raises_uniform_message(email, password):
    service = AuthService(RepoWrongHash(password))
    with pytest.raises(ValueError, match=r"^Credenciales incorrectas\.$"):
        service.login(LoginInput(email=email, username=None, password=password))
