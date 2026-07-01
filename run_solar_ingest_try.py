import os
import sys
import requests
from datetime import datetime, timedelta, UTC

project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from solar_processing.storage import SolarStorageManager

def load_env_from_root():
    dotenv_path = os.path.join(project_root, ".env")
    if os.path.exists(dotenv_path):
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip("'\"")
    else:
        print(f"[WARNING] .env file not found at: {dotenv_path}")

load_env_from_root()

LATITUDE = "43.44608207499594"
LONGITUDE = "-1.5526873172625033"
ORIENTATION = "180"
SLOPE = "27"
FORECAST_DAYS = "1"
TIMEZONE = "utc"
REQUIRED_DATA = "GHI,DHI,BNI,spec_watts,temp,weather_code"

def execute_live_ingest():
    api_key = os.environ.get("PVNODE_API_KEY")
    if not api_key:
        print("[ERROR] PVNODE_API_KEY missing from environment/.env - Aborting")
        return
    
    url = "https://api.pvnode.com/v1/forecast/"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "orientation": ORIENTATION,
        "slope": SLOPE,
        "longitude": LONGITUDE,
        "latitude": LATITUDE,
        "forecast_days": FORECAST_DAYS,
        "timezone": TIMEZONE,
        "required_data": REQUIRED_DATA
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        raw_payload = response.json()
        print(f"[SUCCESS] Received live JSON payload. Records found: {len(raw_payload.get('values', []))}")
    except Exception as e:
        print(f"[ERROR] Live API connection failed: {e}")
        return
    
    storage = SolarStorageManager()
    storage.initialize_storage()

    #today_date = datetime.utcnow().strftime("%Y-%m-%d")
    today_date = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%d")


    success = storage.store_raw_forecast(
        forecast_date=today_date,
        lat=float(LATITUDE),
        lon=float(LONGITUDE),
        payload=raw_payload
    )

    if success:
        saved_data = storage.retrieve_raw_forecast(today_date)
        if saved_data:
            print("[SUCCESS] Data validated! Record was successfully retrieved from MySQL.")
            sample_val = saved_data.get("values", [])[0] if saved_data.get("values") else {}
            print(f"-> Verification Sample: {sample_val}")
        else:
            print("[ERROR] Ingestion indicated success, but verification lookup returned None.")
    else:
        print("[FAIL] Raw JSON payload failed to commit to MySQL.")

if __name__ == "__main__":
    execute_live_ingest()