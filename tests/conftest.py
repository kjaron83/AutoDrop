"""Pytest test fixtures and configuration."""

import os
import sys
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath("."))

# Set test environment before imports
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-testing-purposes-only-32-chars"

from autodrop.core.config import settings
from autodrop.core.database import get_db
from autodrop.core.security import create_session_token, hash_password
from autodrop.main import app
from autodrop.models.base import Base
from autodrop.models.user import User
from autodrop.services.email import clear_test_outbox

# Create in-memory SQLite engine for tests
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Sets up a fresh database schema for every test."""
    clear_test_outbox()
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Provides a transactional database session for tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """Provides FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def verified_user(db: Session) -> User:
    """Creates a verified standard user in the test database."""
    user = User(
        email="customer@autodrop.test",
        hashed_password=hash_password("Password123!"),
        first_name="John",
        last_name="Doe",
        phone="+36301234567",
        is_active=True,
        is_verified=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db: Session) -> User:
    """Creates an admin user in the test database."""
    user = User(
        email="admin@autodrop.test",
        hashed_password=hash_password("AdminPassword123!"),
        first_name="Admin",
        last_name="Superuser",
        phone="+36309876543",
        is_active=True,
        is_verified=True,
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def authenticated_client(client: TestClient, verified_user: User) -> TestClient:
    """Provides TestClient with valid session cookie for verified_user."""
    token = create_session_token({"user_id": verified_user.id})
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)
    return client


@pytest.fixture
def authenticated_admin_client(client: TestClient, admin_user: User) -> TestClient:
    """Provides TestClient with valid session cookie for admin_user."""
    token = create_session_token({"user_id": admin_user.id})
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)
    return client
