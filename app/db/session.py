from sqlalchemy.orm import sessionmaker
from .engine import get_engine

def get_session():
    engine = get_engine()

    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
   