from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
import os

Base = declarative_base()

def get_engine():
    db_url = os.getenv("DATABASE_URL", "sqlite:///./server.db")
    return create_engine(db_url, echo=False, future=True)