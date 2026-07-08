from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register_user(self, payload: UserCreate) -> User:
        email = payload.email.lower()
        if self.users.get_by_email(email) is not None:
            raise UserAlreadyExistsError("A user with this email already exists.")

        try:
            user = self.users.create(
                email=email,
                full_name=payload.full_name,
                hashed_password=hash_password(payload.password),
            )
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as exc:
            self.db.rollback()
            raise UserAlreadyExistsError("A user with this email already exists.") from exc

    def authenticate_user(self, payload: LoginRequest) -> User:
        user = self.users.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password.")
        if not user.is_active:
            raise InactiveUserError("Inactive user account.")
        return user

    def create_user_access_token(self, user: User) -> str:
        return create_access_token(subject=str(user.id))
