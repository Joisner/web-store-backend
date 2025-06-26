import pytest
from typing import Generator, Any
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from alembic.config import Config
from alembic import command

from app.main import app as main_app # Import your FastAPI app
from app.db.base_class import Base
from app.db.session import get_db
from app.core.config import settings
from app.models import * # Import all your models
from app.api.dependencies import get_current_active_user # For overriding dependency

# --- Test Database Setup ---
# Use a separate test database (e.g., SQLite in-memory or a dedicated MySQL test DB)
# Ensure your settings.DATABASE_URL can be overridden by environment variables for tests
# Example: TEST_DATABASE_URL = "sqlite:///./test.db"
# For this example, we'll assume settings.DATABASE_URL is used, but ideally, it's a test-specific URL.
# If using a file-based SQLite DB for tests, ensure it's cleaned up.

# TEST_DATABASE_URL = settings.TEST_DATABASE_URL or "sqlite:///./test.db" # Example
TEST_DATABASE_URL = settings.DATABASE_URL + "_test" # Simple way to create a test DB name if using MySQL/Postgres
# For SQLite in-memory: TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Fixture to manage database schema (create/drop tables) ---
@pytest.fixture(scope="session")
def db_engine():
    """Yield a SQLAlchemy engine for the test database."""
    # Base.metadata.drop_all(bind=engine) # Drop existing tables (optional, depends on strategy)
    Base.metadata.create_all(bind=engine) # Create tables
    yield engine
    Base.metadata.drop_all(bind=engine) # Drop tables after tests
    # If using a file-based SQLite DB:
    # import os
    # if os.path.exists("./test.db"):
    #     os.remove("./test.db")

# --- Fixture for database session, used by tests ---
@pytest.fixture(scope="function")
def db(db_engine) -> Generator[Session, Any, None]:
    """Yield a SQLAlchemy session for a test. Rolls back changes after test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

# --- Fixture for TestClient ---
@pytest.fixture(scope="module")
def client(db) -> Generator[TestClient, Any, None]:
    """Yield a TestClient instance that uses the test database session."""

    def override_get_db():
        try:
            yield db # Use the 'db' fixture session for this test client
        finally:
            pass # DB session is managed by the 'db' fixture itself

    main_app.dependency_overrides[get_db] = override_get_db

    # You might also want to override authentication dependencies for some tests
    # main_app.dependency_overrides[get_current_active_user] = ...

    with TestClient(main_app) as c:
        yield c

    main_app.dependency_overrides.clear() # Clear overrides after module tests


# --- Fixture for creating a test user and getting token (example) ---
from app.schemas.user import UserCreate
from app.services import user_service
from app.core.security import create_access_token

@pytest.fixture(scope="module")
def test_user_data() -> dict:
    return {"email": "testuser@example.com", "password": "testpassword123", "name": "Test User"}

@pytest.fixture(scope="module")
def test_user(db: Session, test_user_data: dict) -> User: # Assuming User model is imported
    user_in = UserCreate(**test_user_data)
    user = user_service.create(db, obj_in=user_in)
    return user

@pytest.fixture(scope="module")
def test_user_token(test_user: User) -> str:
    return create_access_token(subject=test_user.email)

@pytest.fixture
def auth_headers(test_user_token: str) -> dict:
    return {"Authorization": f"Bearer {test_user_token}"}

# --- Optional: Alembic integration for testing migrations ---
# @pytest.fixture(scope="session")
# def apply_migrations():
#     """Applies all Alembic migrations."""
#     alembic_cfg = Config("alembic.ini") # Ensure your alembic.ini points to the test DB URL
#     alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
#     command.upgrade(alembic_cfg, "head")
#     yield
#     # Optionally downgrade after tests, or drop tables
#     # command.downgrade(alembic_cfg, "base")

# If using apply_migrations, you'd adjust db_engine fixture to not create/drop tables via Base.metadata
# and ensure your tests run against a migrated database.

# --- Faker instance for generating test data ---
from faker import Faker
@pytest.fixture(scope="session")
def faker_instance() -> Faker:
    return Faker()

# Note: If your main.py `create_tables()` is uncommented, it might conflict with test setup.
# It's best to manage table creation explicitly for tests or use migrations.
# Ensure your .env or environment variables are set up for testing if your config relies on them.
# (e.g., a different SECRET_KEY for tests, or specific DATABASE_URL for tests).
# The pytest.ini can be used to set environment variables for the test session.
