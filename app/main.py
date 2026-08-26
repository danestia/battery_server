from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone,  timedelta
from app.ingestion import router as ingestion_router
from app.logs import router as logs_router
from app.stats import router as stats_router
from solar_processing.storage import SolarStorageManager

app = FastAPI(
    title="Battery Tracker Hub",
    description="Receives and stores battery logs from spoke machines",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
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

@app.get("/api/v1/instructions/tomorrow", response_model=dict[int, float])
def get_tomorrow_instructions():
    tomorrow_str = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

    storage = SolarStorageManager()

    raw_payload = storage.get_hourly_instructions_for_date(tomorrow_str)

    if not raw_payload:
        raise HTTPException(
            status_code=404,
            detail=f"Hourly charging instructions for {tomorrow_str} have not been generated yet"
        )
    
    scaled_payload = {}
    for h in range(24):
        pct_val = raw_payload.get(h, 0.0)
        decimal_val = float(pct_val) / 100.0
        scaled_payload[h] = round(max(0.0, min(1.0, decimal_val)), 3)

    from solar_processing.packer import PiInstructionPacker
    plantform_payload = PiInstructionPacker.slice_working_hours(scaled_payload)

    return plantform_payload