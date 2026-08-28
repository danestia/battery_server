import os
import sys
import logging
from datetime import timedelta, date

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

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
        logging.warning(f".env file not found at: {dotenv_path}")

load_env_from_root()

from solar_processing.ingest import SolarIngestPipeline
from solar_processing.storage import SolarStorageManager

def main():
    api_key = os.environ.get("PVNODE_API_KEY")
    if not api_key:
        logging.error("PVNODE_API_KEY missing from environment configuration.")
        sys.exit(1)

    LATITUDE = 43.44608207499594
    LONGITUDE = -1.5526873172625033
    ORIENTATION = 180.0
    SLOPE = 27.0

    pipeline = SolarIngestPipeline(api_key=api_key, lat=LATITUDE, lon=LONGITUDE)
    
    processed_data = pipeline.run_advance_pipeline(slope=SLOPE, orientation=ORIENTATION, forecast_days=1)
    
    if processed_data is not None:
        logging.info("--- PIPELINE VERIFICATION SUCCESSFUL ---")
        logging.info(f"DataFrame Shape: {processed_data.shape}")
        logging.info(f"Available Columns: {list(processed_data.columns)}")

        logging.info("Aggregating 15 minute physical metrics to hourly values...")

        import pandas as pd
        if not isinstance(processed_data.index, pd.DatetimeIndex):
            processed_data.index = pd.to_datetime(processed_data.index)

        hourly_series = processed_data.groupby(processed_data.index.hour)['power_percentage'].mean() / 100.0

        hourly_averages = hourly_series.clip(lower=0.0, upper=1.0).round(4).to_dict()
        #tomorrow_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow_str = date.today()


        logging.info(f"Saving hourly instructions to database for {tomorrow_str}...")

        storage = SolarStorageManager()
        storage.store_hourly_instructions(tomorrow_str, hourly_averages)

        logging.info("--- DATABASE WRITES COMPLETED SUCCESSFULLY ---")
    
    else:
        logging.error("Pipeline run encountered fatal execution blocks")
        sys.exit(1)

if __name__ == "__main__":
    main()