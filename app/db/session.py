from sqlalchemy.orm import sessionmaker
from .engine import get_engine

def get_session():
    engine = get_engine()
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    return SessionLocal()