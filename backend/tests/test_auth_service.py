from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.db.base import Base
from app.models.enums import UserRole
from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_register_user_creates_viewer_with_hashed_password(db_session: Session) -> None:
    service = AuthService(db_session)

    user = service.register_user(
        UserCreate(
            email="BHAVANA@example.com",
            full_name="Bhavana Hegde",
            password="secure-password",
        )
    )

    assert user.email == "bhavana@example.com"
    assert user.full_name == "Bhavana Hegde"
    assert user.role == UserRole.VIEWER
    assert user.hashed_password != "secure-password"


def test_register_user_rejects_duplicate_email(db_session: Session) -> None:
    service = AuthService(db_session)
    payload = UserCreate(
        email="bhavana@example.com",
        full_name="Bhavana Hegde",
        password="secure-password",
    )

    service.register_user(payload)

    with pytest.raises(UserAlreadyExistsError):
        service.register_user(payload)


def test_authenticate_user_accepts_valid_credentials(db_session: Session) -> None:
    service = AuthService(db_session)
    service.register_user(
        UserCreate(
            email="bhavana@example.com",
            full_name="Bhavana Hegde",
            password="secure-password",
        )
    )

    user = service.authenticate_user(
        LoginRequest(email="bhavana@example.com", password="secure-password")
    )
    token = service.create_user_access_token(user)

    assert user.email == "bhavana@example.com"
    assert token.count(".") == 2


def test_authenticate_user_rejects_invalid_password(db_session: Session) -> None:
    service = AuthService(db_session)
    service.register_user(
        UserCreate(
            email="bhavana@example.com",
            full_name="Bhavana Hegde",
            password="secure-password",
        )
    )

    with pytest.raises(InvalidCredentialsError):
        service.authenticate_user(
            LoginRequest(email="bhavana@example.com", password="wrong-password")
        )
