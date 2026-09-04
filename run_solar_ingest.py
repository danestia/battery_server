import logging
import os
import sys
from datetime import date, timedelta
from dotenv import load_dotenv

from solar_processing.ingest import SolarIngestPipeline
from solar_processing.packer import PiInstructionPacker
from solar_processing.storage import SolarStorageManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("run_ingest")

load_dotenv()


def main() -> None:
    """Runs the primary solar ingest pipeline, calculates hourly instructions, and stores targets."""
    api_key = os.getenv("PVNODE_API_KEY")
    if not api_key:
        logger.error("PVNODE_API_KEY missing from environment configuration.")
        sys.exit(1)

    latitude = float(os.getenv("SOLAR_LATITUDE", "43.44608207499594"))
    longitude = float(os.getenv("SOLAR_LONGITUDE", "-1.5526873172625033"))
    orientation = float(os.getenv("SOLAR_ORIENTATION", "180.0"))
    slope = float(os.getenv("SOLAR_SLOPE", "27.0"))

    pipeline = SolarIngestPipeline(api_key=api_key, lat=latitude, lon=longitude)

    processed_data = pipeline.run_advance_pipeline(
        slope=slope, orientation=orientation, forecast_days=1
    )

    if processed_data is not None and not processed_data.empty:
        logger.info("--- PIPELINE VERIFICATION SUCCESSFUL ---")
        logger.info(f"DataFrame Shape: {processed_data.shape}")

        hourly_payload = PiInstructionPacker.to_hourly_payload(processed_data)

        # Target date is tomorrow's forecast date
        tomorrow_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        logger.info(f"Saving hourly instructions to database for {tomorrow_str}...")

        storage = SolarStorageManager()
        storage.store_hourly_instructions(tomorrow_str, hourly_payload)

        logger.info("--- DATABASE WRITES COMPLETED SUCCESSFULLY ---")
    else:
        logger.error("Pipeline run encountered fatal execution blocks or empty output.")
        sys.exit(1)


if __name__ == "__main__":
    main()