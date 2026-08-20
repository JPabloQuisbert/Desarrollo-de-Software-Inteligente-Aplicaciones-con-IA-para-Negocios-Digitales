from extensions import db


class User(db.Model):
    """Representa un usuario en la base de datos."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def __repr__(self) -> str:
        return f"<User {self.username}>"
