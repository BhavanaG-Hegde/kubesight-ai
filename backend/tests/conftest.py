from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import get_settings
from app.db.base import Base
from app.main import create_app


@pytest.fixture()
def db_engine() -> Generator[Engine, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_engine: Engine, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("BACKGROUND_WORKER_ENABLED", "false")
    get_settings.cache_clear()

    app = create_app()
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "api-user@example.com",
            "full_name": "API User",
            "password": "secure-password",
        },
    )
    assert register_response.status_code == 201

    token_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "api-user@example.com",
            "password": "secure-password",
        },
    )
    assert token_response.status_code == 200

    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
