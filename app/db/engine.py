import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        db_url = os.getenv("DATABASE_URL")
        if db_url is None:
            raise RuntimeError("DATABASE_URL environment variable is not set")
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        _engine = create_engine(db_url, echo=False, future=True, connect_args=connect_args)
    return _engine