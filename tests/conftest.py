import os
if os.path.exists("test.db"):
    os.remove("test.db")

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.db.base import Base, get_engine
from app.db.session import SessionLocal
from app.main import app

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Recreate global engine for tests
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    engine = get_engine()
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client(db_session):

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides.clear()
    app.dependency_overrides[app.ingestion.get_db] = override_get_db

    return TestClient(app)
