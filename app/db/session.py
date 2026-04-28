from sqlalchemy.orm import sessionmaker
from .base import get_engine

engine = get_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)