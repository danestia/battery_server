from fastapi import FastAPI, HTTPException
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

    query = """
        SELECT hour_index, charge_target_pct
        FROM pi_hourly_instructions
        WHERE target_date = %s
        ORDER BY hour_index ASC;
    """

    conn = None
    cursor = None
    try:
        conn = storage._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (tomorrow_str,))
        rows = cursor.fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"Hourly charging instructions for {tomorrow_str} have not been generated yet"
            )
        
        return{int(hour): float(pct) for hour, pct in rows}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] Database retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Internal database server failure")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
