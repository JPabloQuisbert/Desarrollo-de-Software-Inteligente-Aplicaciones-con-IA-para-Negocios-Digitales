import re
from dataclasses import dataclass


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class RegisterInput:
    username: str
    email: str
    password: str


@dataclass
class LoginInput:
    password: str
    email: str | None = None
    username: str | None = None


class UserValidator:
    """Valida los campos de entrada del usuario. Solo responsabilidad: validar."""

    def validate_register(self, data: dict) -> RegisterInput:
        username = (data.get("username") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        if not username:
            raise ValueError("El nombre de usuario es requerido.")
        if len(username) < 3:
            raise ValueError("El nombre de usuario debe tener al menos 3 caracteres.")
        if not email or not EMAIL_REGEX.match(email):
            raise ValueError("El correo electrónico no es válido.")
        if not password or len(password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")

        return RegisterInput(username=username, email=email, password=password)

    def validate_login(self, data: dict) -> LoginInput:
        email_raw = (data.get("email") or "").strip().lower()
        username_raw = (data.get("username") or "").strip()
        password = data.get("password") or ""

        email: str | None = None
        username: str | None = None

        if email_raw:
            if not EMAIL_REGEX.match(email_raw):
                raise ValueError("El correo electrónico no es válido.")
            email = email_raw
        elif username_raw:
            if len(username_raw) < 3:
                raise ValueError("El nombre de usuario debe tener al menos 3 caracteres.")
            username = username_raw
        else:
            raise ValueError("Debes proporcionar un correo electrónico o nombre de usuario.")

        if not password:
            raise ValueError("La contraseña es requerida.")

        return LoginInput(password=password, email=email, username=username)
