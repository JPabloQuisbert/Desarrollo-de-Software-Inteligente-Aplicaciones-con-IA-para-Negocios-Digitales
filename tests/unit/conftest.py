"""
Hypothesis strategies shared across unit tests for the user-login feature.

Strategies defined here:
  - valid_email_st       : emails that match ^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$
  - invalid_email_st     : strings that are non-empty after strip but do NOT match the regex
  - valid_username_st    : stripped strings with at least 3 characters (max 80)
  - short_username_st    : strings whose stripped length is < 3 (includes empty string)
  - nonempty_password_st : non-empty strings up to 128 characters
"""

import re

from hypothesis import strategies as st

# Same pattern used by UserValidator in schemas/user_schema.py
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# ---------------------------------------------------------------------------
# valid_email_st
# Generates strings that fully match the email regex.
# st.from_regex with fullmatch=True is more efficient than filtering random
# text because it constructs conforming examples directly from the grammar.
# ---------------------------------------------------------------------------
valid_email_st = st.from_regex(r"[^@\s]+@[^@\s]+\.[^@\s]+", fullmatch=True)

# ---------------------------------------------------------------------------
# invalid_email_st
# Generates non-empty (after strip) strings that do NOT pass the email regex.
# ---------------------------------------------------------------------------
invalid_email_st = st.text().filter(
    lambda s: bool(s.strip()) and not EMAIL_REGEX.match(s.strip().lower())
)

# ---------------------------------------------------------------------------
# valid_username_st
# Generates strings that, after stripping, have at least 3 characters.
# max_size=80 mirrors the User.username column length.
# ---------------------------------------------------------------------------
valid_username_st = (
    st.text(min_size=3, max_size=80)
    .map(str.strip)
    .filter(lambda s: len(s) >= 3)
)

# ---------------------------------------------------------------------------
# short_username_st
# Generates strings whose stripped length is 0, 1, or 2 (always too short).
# max_size=2 on the raw text guarantees strip() never yields 3+ chars.
# ---------------------------------------------------------------------------
short_username_st = st.text(max_size=2)

# ---------------------------------------------------------------------------
# nonempty_password_st
# Generates non-empty passwords up to 128 characters.
# ---------------------------------------------------------------------------
nonempty_password_st = st.text(min_size=1, max_size=128)
