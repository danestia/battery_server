from sqlalchemy.orm import sessionmaker
from .engine import get_engine

def get_session():
    engine = get_engine()

    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
   
def get_db():
    SessionLocal = get_session()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()