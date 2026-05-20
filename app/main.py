from fastapi import FastAPI
from datetime import datetime, timezone
from app.ingestion import router as ingestion_router
from app.logs import router as logs_router
from app.stats import router as stats_router

app = FastAPI(
    title="Battery Tracker Hub",
    description="Receives and stores battery logs from spoke machines",
    version="0.1.0",
)

app.include_router(ingestion_router)
app.include_router(logs_router)
app.include_router(stats_router)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

