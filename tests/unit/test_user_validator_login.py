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

from modules.auth.schema import EMAIL_REGEX, LoginInput, UserValidator
from tests.unit.conftest import (
    invalid_email_st,
    nonempty_password_st,
    short_username_st,
    valid_email_st,
    valid_username_st,
)

validator = UserValidator()


# Feature: user-login, Property 3: short username is always rejected
@given(username=short_username_st, password=nonempty_password_st)
@settings(max_examples=100)
def test_short_username_always_rejected(username, password):
    data = {"username": username, "password": password}
    with pytest.raises(ValueError):
        validator.validate_login(data)


# Feature: user-login, Property 1: missing identifier always produces the correct error
@given(password=nonempty_password_st)
@settings(max_examples=100)
def test_no_identifier_raises_correct_error(password):
    data = {"password": password}
    with pytest.raises(ValueError):
        validator.validate_login(data)


# Feature: user-login, Property 2: invalid email format is always rejected
@given(email=invalid_email_st, password=nonempty_password_st)
@settings(max_examples=100)
def test_invalid_email_always_rejected(email, password):
    data = {"email": email, "password": password}
    with pytest.raises(ValueError):
        validator.validate_login(data)


# Feature: user-login, Property 5: input normalization — email
@given(
    email=valid_email_st,
    padding=st.text(alphabet=" 	", max_size=3),
    password=nonempty_password_st,
)
@settings(max_examples=100)
def test_email_normalization(email, padding, password):
    raw_email = padding + email + padding
    data = {"email": raw_email, "password": password}
    result = validator.validate_login(data)
    assert result.email == raw_email.strip().lower()
    assert result.username is None


# Feature: user-login, Property 5: input normalization — username
@given(
    username=valid_username_st,
    padding=st.text(alphabet=" ", max_size=3),
    password=nonempty_password_st,
)
@settings(max_examples=100)
def test_username_normalization(username, padding, password):
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
    data_absent = {"email": email}
    with pytest.raises(ValueError):
        validator.validate_login(data_absent)

    data_with = {"email": email, "password": bad_password}
    with pytest.raises(ValueError):
        validator.validate_login(data_with)
