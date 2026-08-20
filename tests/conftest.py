import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db as _db
from models.user import User


@pytest.fixture(scope="session")
def app():
    """Create a Flask application configured for testing (in-memory SQLite)."""
    application = create_app("testing")
    return application


@pytest.fixture(scope="session")
def client(app):
    """Return a Flask test client for the application."""
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app):
    """
    Create all tables before each test and drop them afterwards,
    providing a clean database state per test.
    """
    with app.app_context():
        _db.create_all()
        yield _db.session
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def seeded_user(db_session, app):
    """
    Insert a generic pre-registered user into the database.
    Returns the User ORM instance.
    """
    with app.app_context():
        user = User(
            username="testuser",
            email="testuser@example.com",
            password_hash=generate_password_hash("password123"),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user


@pytest.fixture(scope="function")
def seeded_login_user(db_session, app):
    """
    Insert a user suitable for login tests.
    Returns a tuple of (User, plaintext_password) so tests have access
    to both the ORM record and the known credentials.
    """
    plaintext_password = "secret123"
    with app.app_context():
        user = User(
            username="loginuser",
            email="loginuser@example.com",
            password_hash=generate_password_hash(plaintext_password),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return (user, plaintext_password)
