from typing import Generator
from sqlalchemy.orm import sessionmaker, Session
from .engine import get_engine

engine = get_engine()
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()