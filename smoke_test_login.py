"""
smoke_test_login.py
-------------------
Smoke-tests for the POST /auth/login endpoint.
Uses Flask's built-in test client with an in-memory SQLite database so no
running server or external tooling is required.

Scenarios verified
------------------
1. Login with email + correct password  â†’ 200, access_token present, no password_hash
2. Login with username + correct password â†’ 200, access_token present, no password_hash
3. Login with correct email but wrong password â†’ 401, "Credenciales incorrectas."
4. Login with no identifier (no email, no username) â†’ 400
"""

import json
import sys
import os

# Make sure project root is on the path so absolute imports work.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from extensions import db as _db
from werkzeug.security import generate_password_hash


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "âœ“"
FAIL = "âœ—"

results = []


def check(label: str, condition: bool, detail: str = ""):
    symbol = PASS if condition else FAIL
    msg = f"  [{symbol}] {label}"
    if detail:
        msg += f"  â€” {detail}"
    print(msg)
    results.append((label, condition))


def post_login(client, payload):
    return client.post(
        "/auth/login",
        data=json.dumps(payload),
        content_type="application/json",
    )


# ---------------------------------------------------------------------------
# Test setup: create app with in-memory DB and seed one user
# ---------------------------------------------------------------------------

# Override the DB URI *before* create_app so SQLAlchemy uses in-memory SQLite.
os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

app = create_app("default")
app.config["TESTING"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

TEST_USERNAME = "johndoe"
TEST_EMAIL = "john@example.com"
TEST_PASSWORD = "secret123"

with app.app_context():
    _db.drop_all()   # wipe any state from previous runs
    _db.create_all()
    # Seed a test user directly so we don't depend on the register endpoint.
    from modules.auth.model import User
    user = User(
        username=TEST_USERNAME,
        email=TEST_EMAIL,
        password_hash=generate_password_hash(TEST_PASSWORD),
    )
    _db.session.add(user)
    _db.session.commit()

client = app.test_client()

# ---------------------------------------------------------------------------
# Scenario 1 â€” Login with email + correct password
# ---------------------------------------------------------------------------
print("\nScenario 1: Login with email + correct password")
resp = post_login(client, {"email": TEST_EMAIL, "password": TEST_PASSWORD})
body = resp.get_json()

check("HTTP status is 200", resp.status_code == 200, f"got {resp.status_code}")
check("access_token is present", "access_token" in body, str(body.keys()))
check("id is present", "id" in body)
check("username is present", "username" in body)
check("email is present", "email" in body)
check("password_hash is absent", "password_hash" not in body)

# ---------------------------------------------------------------------------
# Scenario 2 â€” Login with username + correct password
# ---------------------------------------------------------------------------
print("\nScenario 2: Login with username + correct password")
resp = post_login(client, {"username": TEST_USERNAME, "password": TEST_PASSWORD})
body = resp.get_json()

check("HTTP status is 200", resp.status_code == 200, f"got {resp.status_code}")
check("access_token is present", "access_token" in body, str(body.keys()))
check("id is present", "id" in body)
check("username matches", body.get("username") == TEST_USERNAME)
check("password_hash is absent", "password_hash" not in body)

# ---------------------------------------------------------------------------
# Scenario 3 â€” Correct email, wrong password â†’ 401
# ---------------------------------------------------------------------------
print("\nScenario 3: Correct email, wrong password")
resp = post_login(client, {"email": TEST_EMAIL, "password": "wrongpassword"})
body = resp.get_json()

check("HTTP status is 401", resp.status_code == 401, f"got {resp.status_code}")
check(
    'Error message is "Credenciales incorrectas."',
    body.get("error") == "Credenciales incorrectas.",
    repr(body.get("error")),
)
check("password_hash is absent", "password_hash" not in body)

# ---------------------------------------------------------------------------
# Scenario 4 â€” No identifier provided â†’ 400
# ---------------------------------------------------------------------------
print("\nScenario 4: No identifier (no email, no username)")
resp = post_login(client, {"password": TEST_PASSWORD})
body = resp.get_json()

check("HTTP status is 400", resp.status_code == 400, f"got {resp.status_code}")
check("error field is present", "error" in body, str(body))
check("password_hash is absent", "password_hash" not in body)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 50)
passed = sum(1 for _, ok in results if ok)
total = len(results)
print(f"Results: {passed}/{total} checks passed")

if passed < total:
    print("\nFailed checks:")
    for label, ok in results:
        if not ok:
            print(f"  {FAIL} {label}")
    sys.exit(1)
else:
    print("All checks passed.")
    sys.exit(0)
