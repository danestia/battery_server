from fastapi import FastAPI
from app.db.base import Base, get_engine
from app.ingestion import router as ingestion_router

engine = get_engine()
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(ingestion_router)