import os
import sys
import logging

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
        
        print("\n--- FIRST 5 ROWS OF PROCESSED METRICS ---")
        print(processed_data.head(5))
    else:
        logging.error("Pipeline run encountered fatal execution blocks.")
        sys.exit(1)

if __name__ == "__main__":
    main()