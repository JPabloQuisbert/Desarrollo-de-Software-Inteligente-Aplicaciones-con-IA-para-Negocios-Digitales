"""
Property-based and example tests for AuthService.login.

Tests are organized by the correctness properties defined in the design doc:
  Property 6  — Lookup is routed to the correct repository method           (task 4.2)
  Property 7  — Credential failure is always reported with the same message (task 4.3)

Stub repositories defined here:
  RepoNone       — find_by_email / find_by_username always return None.
  RepoWrongHash  — find_by_email returns a User whose password_hash does not
                   match the LoginInput password; find_by_username returns None.
  RepoByField    — configurable stub that returns a User from one specific
                   lookup method and None from the other, recording every call.
"""

from werkzeug.security import generate_password_hash

from models.user import User
from schemas.user_schema import LoginInput
from services.auth_service import AuthService


# ---------------------------------------------------------------------------
# Helper: build a detached User instance without hitting the database.
# User.__new__(User) skips __init__ and SQLAlchemy instrumentation so the
# object can be used freely in pure-unit tests.
# ---------------------------------------------------------------------------

def _make_user(
    id: int = 1,
    username: str = "testuser",
    email: str = "test@example.com",
    password_hash: str = "",
) -> User:
    """Return a lightweight User stub without a database session."""
    user = User.__new__(User)
    user.id = id
    user.username = username
    user.email = email
    user.password_hash = password_hash
    return user


# ---------------------------------------------------------------------------
# RepoNone
# Every lookup returns None — simulates a database with no matching account.
# ---------------------------------------------------------------------------

class RepoNone:
    """Stub repository where no user is ever found."""

    def find_by_email(self, email: str) -> None:
        return None

    def find_by_username(self, username: str) -> None:
        return None


# ---------------------------------------------------------------------------
# RepoWrongHash
# find_by_email returns a User whose password_hash was generated from a
# *different* string, so check_password_hash always returns False.
# find_by_username returns None (email-path tests use this repo).
# ---------------------------------------------------------------------------

class RepoWrongHash:
    """
    Stub repository that returns a User with a mismatching password hash.

    Constructed with the *correct* password so it can produce a hash that is
    guaranteed to differ: ``generate_password_hash("different_" + password)``.
    """

    def __init__(self, password: str) -> None:
        self._hash = generate_password_hash("different_" + password)

    def find_by_email(self, email: str) -> User:
        return _make_user(email=email, password_hash=self._hash)

    def find_by_username(self, username: str) -> None:
        return None


# ---------------------------------------------------------------------------
# RepoByField
# Returns a valid User (with a correct hash for a known password) from exactly
# one lookup method; the other method always returns None.
# Every call to either method is appended to ``called_methods`` so tests can
# assert which path was taken.
# ---------------------------------------------------------------------------

_REPO_BY_FIELD_KNOWN_PASSWORD = "correct_password"


class RepoByField:
    """
    Configurable stub repository that routes results to a single lookup method.

    Parameters
    ----------
    active_field : str
        Either ``"email"`` or ``"username"``.  The corresponding lookup method
        returns a user; the other returns ``None``.

    Attributes
    ----------
    called_methods : list[str]
        Ordered list of method names that were called (``"find_by_email"`` or
        ``"find_by_username"``).  Reset between instantiations.

    Notes
    -----
    The returned User always has ``password_hash`` set to
    ``generate_password_hash(_REPO_BY_FIELD_KNOWN_PASSWORD)`` so that an
    ``AuthService.login`` call with the matching password succeeds end-to-end
    when desired (though property tests for routing intentionally use
    ``RepoNone``-style expectations and will catch ``ValueError`` from auth
    failure — the routing assertion is what matters there).
    """

    def __init__(self, active_field: str) -> None:
        if active_field not in ("email", "username"):
            raise ValueError("active_field must be 'email' or 'username'")
        self._active_field = active_field
        self._hash = generate_password_hash(_REPO_BY_FIELD_KNOWN_PASSWORD)
        self.called_methods: list[str] = []

    def find_by_email(self, email: str) -> User | None:
        self.called_methods.append("find_by_email")
        if self._active_field == "email":
            return _make_user(email=email, password_hash=self._hash)
        return None

    def find_by_username(self, username: str) -> User | None:
        self.called_methods.append("find_by_username")
        if self._active_field == "username":
            return _make_user(username=username, password_hash=self._hash)
        return None


# ---------------------------------------------------------------------------
# TODO (task 4.2): Property 6 — lookup is routed to the correct repository method
# TODO (task 4.3): Property 7 — credential failure prevents account enumeration
# ---------------------------------------------------------------------------
