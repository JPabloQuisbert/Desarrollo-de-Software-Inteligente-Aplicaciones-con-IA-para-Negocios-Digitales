from werkzeug.security import generate_password_hash, check_password_hash

from models.user import User
from schemas.user_schema import RegisterInput, LoginInput
from repositories.user_repository import UserRepository


class AuthService:
    """Lógica de negocio de autenticación. Solo responsabilidad: reglas de negocio."""

    def __init__(self, user_repository: UserRepository):
        self._repo = user_repository

    def register(self, input_data: RegisterInput) -> User:
        if self._repo.find_by_email(input_data.email):
            raise ValueError("Ya existe una cuenta con ese correo electrónico.")
        if self._repo.find_by_username(input_data.username):
            raise ValueError("El nombre de usuario ya está en uso.")

        user = User(
            username=input_data.username,
            email=input_data.email,
            password_hash=generate_password_hash(input_data.password),
        )
        return self._repo.save(user)

    def login(self, input_data: LoginInput) -> User:
        if input_data.email:
            user = self._repo.find_by_email(input_data.email)
        else:
            user = self._repo.find_by_username(input_data.username)

        if not user or not check_password_hash(user.password_hash, input_data.password):
            raise ValueError("Credenciales incorrectas.")
        return user
