from modules.auth.model import User
from extensions import db


class UserRepository:
    """Acceso a datos del usuario. Solo responsabilidad: persistencia."""

    def find_by_email(self, email: str) -> User | None:
        return User.query.filter_by(email=email).first()

    def find_by_username(self, username: str) -> User | None:
        return User.query.filter_by(username=username).first()

    def save(self, user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user
