import os
import pytest
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///file:testdb?mode=memory&cache=shared&uri=true"

from app.db.base import Base
from app.db.engine import get_engine
from app.main import app

@pytest.fixture(scope="session")
def engine():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(engine):
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.expire_all()
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    from app.ingestion import get_db as ingestion_get_db
    from app.logs import get_db as logs_get_db
    from app.db.session import get_db as session_get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass
        
    app.dependency_overrides[ingestion_get_db] = override_get_db
    app.dependency_overrides[logs_get_db] = override_get_db
    app.dependency_overrides[session_get_db] = override_get_db

    yield TestClient(app)
    app.dependency_overrides.clear()