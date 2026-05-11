import os
from sqlalchemy import create_engine

def get_engine():
    db_url = os.getenv("DATABASE_URL", "sqlite:///./server.db")
    return create_engine(db_url, echo=False, future=True)