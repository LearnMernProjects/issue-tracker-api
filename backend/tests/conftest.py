"""
Configuration for pytest tests.
"""
import os
os.environ["TESTING"] = "true"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app import models  # Import models to register them with Base
from app.main import app


# Use SQLite in-memory database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test database tables once per session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with test database."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db):
    """Create a sample user for testing."""
    from app.crud.users import create_user
    from app.schemas import UserCreate
    
    user = create_user(db, UserCreate(name="Test User", email="test@example.com"))
    return user


@pytest.fixture
def sample_assignee(db):
    """Create a sample assignee user for testing."""
    from app.crud.users import create_user
    from app.schemas import UserCreate
    
    user = create_user(db, UserCreate(name="Assignee", email="assignee@example.com"))
    return user


@pytest.fixture
def sample_issue(db, sample_user):
    """Create a sample issue for testing."""
    from app.crud.issues import create_issue
    from app.schemas import IssueCreate
    
    issue = create_issue(db, IssueCreate(
        title="Sample Issue",
        description="This is a test issue",
        creator_id=sample_user.id
    ))
    return issue
