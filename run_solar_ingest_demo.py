import logging
import os
import sys
from datetime import UTC, datetime, timedelta
from dotenv import load_dotenv
import requests

from solar_processing.storage import SolarStorageManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("test_live_ingest")

load_dotenv()

LATITUDE = float(os.getenv("SOLAR_LATITUDE", "43.44608207499594"))
LONGITUDE = float(os.getenv("SOLAR_LONGITUDE", "-1.5526873172625033"))
ORIENTATION = os.getenv("SOLAR_ORIENTATION", "180")
SLOPE = os.getenv("SOLAR_SLOPE", "27")
FORECAST_DAYS = "1"
TIMEZONE = "utc"
REQUIRED_DATA = "GHI,DHI,BNI,spec_watts,temp,weather_code"


def execute_live_ingest() -> bool:
    """Executes a end-to-end smoke test fetching raw PVNode forecast data and verifying DB persistence."""
    api_key = os.getenv("PVNODE_API_KEY")
    if not api_key:
        logger.error("PVNODE_API_KEY missing from environment configuration - Aborting")
        return False

    url = "https://api.pvnode.com/v1/forecast/"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "orientation": ORIENTATION,
        "slope": SLOPE,
        "longitude": str(LONGITUDE),
        "latitude": str(LATITUDE),
        "forecast_days": FORECAST_DAYS,
        "timezone": TIMEZONE,
        "required_data": REQUIRED_DATA,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        raw_payload = response.json()
        logger.info(
            f"Received live JSON payload. Records found: {len(raw_payload.get('values', []))}"
        )
    except Exception as e:
        logger.error(f"Live API connection failed: {e}")
        return False

    storage = SolarStorageManager()
    storage.initialize_storage()

    target_date = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%d")

    success = storage.store_raw_forecast(
        forecast_date=target_date,
        lat=LATITUDE,
        lon=LONGITUDE,
        payload=raw_payload,
    )

    if success:
        saved_data = storage.retrieve_raw_forecast(target_date)
        if saved_data:
            logger.info("Data validated! Record successfully retrieved from MySQL.")
            sample_val = saved_data.get("values", [])[0] if saved_data.get("values") else {}
            logger.info(f"Verification Sample: {sample_val}")
            return True
        else:
            logger.error("Ingestion succeeded, but verification lookup returned None.")
            return False
    else:
        logger.error("Raw JSON payload failed to commit to MySQL.")
        return False


if __name__ == "__main__":
    sys.exit(0 if execute_live_ingest() else 1)