from fastapi import FastAPI
from app.ingestion import router as ingestion_router

app = FastAPI()
app.include_router(ingestion_router)