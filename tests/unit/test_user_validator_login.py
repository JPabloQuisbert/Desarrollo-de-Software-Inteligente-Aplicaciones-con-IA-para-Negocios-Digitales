"""
Property-based and example tests for UserValidator.validate_login.

Tests are organized by the correctness properties defined in the design doc:
  Property 1  -- Missing identifier always produces the correct error        (task 2.2)
  Property 2  -- Invalid email format is always rejected                     (task 2.3)
  Property 3  -- Short username is always rejected                           (task 2.4)
  Property 4  -- Empty or absent password is always rejected                 (task 2.5)
  Property 5  -- Input normalization is applied consistently                 (task 2.6)
"""

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from schemas.user_schema import EMAIL_REGEX, LoginInput, UserValidator
from tests.unit.conftest import (
    invalid_email_st,
    nonempty_password_st,
    short_username_st,
    valid_email_st,
    valid_username_st,
)

# ---------------------------------------------------------------------------
# Module-level validator instance shared across all tests in this file.
# ---------------------------------------------------------------------------
validator = UserValidator()

# ---------------------------------------------------------------------------
# TODO (task 2.6): Property 5 -- input normalization is applied consistently
# ---------------------------------------------------------------------------


# Feature: user-login, Property 3: short username is always rejected
@given(username=short_username_st, password=nonempty_password_st)
@settings(max_examples=100)
def test_short_username_always_rejected(username, password):
    """**Validates: Requirements 2.3**

    For any string whose stripped length is < 3 (including empty string),
    together with a non-empty password and no email field, validate_login
    must always raise ValueError — either "missing identifier" (stripped
    to empty) or "username too short" (stripped to 1-2 chars).  Both are
    correct rejections; the key invariant is that the call never succeeds.
    """
    data = {"username": username, "password": password}
    with pytest.raises(ValueError):
        validator.validate_login(data)


# Feature: user-login, Property 1: missing identifier always produces the correct error
@given(password=nonempty_password_st)
@settings(max_examples=100)
def test_no_identifier_raises_correct_error(password):
    """**Validates: Requirements 2.1**

    For any dict containing a non-empty password but neither a non-empty
    email nor a non-empty username, validate_login must raise ValueError
    with the missing-identifier message.
    """
    data = {"password": password}
    with pytest.raises(ValueError, match="Debes proporcionar un correo electrónico o nombre de usuario"):
        validator.validate_login(data)


# Feature: user-login, Property 2: invalid email format is always rejected
@given(email=invalid_email_st, password=nonempty_password_st)
@settings(max_examples=100)
def test_invalid_email_always_rejected(email, password):
    """**Validates: Requirements 2.2**

    For any string that does not match ^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$ (after
    strip + lowercase), provided alongside a non-empty password, validate_login
    must raise ValueError("El correo electronico no es valido.").
    """
    data = {"email": email, "password": password}
    with pytest.raises(ValueError, match="El correo electr\u00f3nico no es v\u00e1lido"):
        validator.validate_login(data)


# Feature: user-login, Property 5: input normalization is applied consistently
@given(
    email=valid_email_st,
    padding=st.text(alphabet=" \t", max_size=3),
    password=nonempty_password_st,
)
@settings(max_examples=100)
def test_email_normalization(email, padding, password):
    """**Validates: Requirements 2.6**

    For any valid email (including leading/trailing whitespace or uppercase
    letters), validate_login must return a LoginInput where
    email == raw_email.strip().lower() and username is None.
    """
    raw_email = padding + email + padding
    data = {"email": raw_email, "password": password}
    result = validator.validate_login(data)
    assert result.email == raw_email.strip().lower()
    assert result.username is None


# Feature: user-login, Property 5: input normalization is applied consistently
@given(
    username=valid_username_st,
    padding=st.text(alphabet=" ", max_size=3),
    password=nonempty_password_st,
)
@settings(max_examples=100)
def test_username_normalization(username, padding, password):
    """**Validates: Requirements 2.6**

    For any valid username (including leading/trailing whitespace),
    validate_login must return a LoginInput where
    username == raw_username.strip() and email is None.
    """
    raw_username = padding + username + padding
    assume(len(raw_username.strip()) >= 3)
    data = {"username": raw_username, "password": password}
    result = validator.validate_login(data)
    assert result.username == raw_username.strip()
    assert result.email is None


# Feature: user-login, Property 4: empty or absent password is always rejected
@given(
    email=valid_email_st,
    bad_password=st.one_of(st.just(""), st.just(None), st.none()),
)
@settings(max_examples=100)
def test_empty_password_always_rejected(email, bad_password):
    """**Validates: Requirements 2.4**

    For any dict containing a valid email identifier but with password absent,
    None, or empty string, validate_login must raise ValueError("La contraseña
    es requerida.").
    """
    # Case 1: password key is absent entirely
    data_absent = {"email": email}
    with pytest.raises(ValueError, match="La contrase\u00f1a es requerida"):
        validator.validate_login(data_absent)

    # Case 2: password key is present but empty or None
    data_with = {"email": email, "password": bad_password}
    with pytest.raises(ValueError, match="La contrase\u00f1a es requerida"):
        validator.validate_login(data_with)
