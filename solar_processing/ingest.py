import logging
from datetime import datetime, timedelta, UTC
import pandas as pd

from solar_processing.storage import SolarStorageManager
from solar_processing.interpreter import SolarDataInterpreter

logger = logging.getLogger("solar_processing.ingest")

class SolarIngestPipeline:

    def __init__(self, api_key: str, lat: float, lon: float):
        self.api_key = api_key
        self.lat = lat
        self.lon = lon

        self.storage = SolarStorageManager()
        self.interpreter = SolarDataInterpreter(lat=self.lat, lon=self.lon)

    def run_advance_pipeline(self, slope: float, orientation: float, forecast_days: int = 1) -> pd.DataFrame | None:
        import requests
        logger.info(f"Initiating advance solar pipeline for coordinates: ({self.lat}, {self.lon})")

        url = "https://api.pvnode.com/v1/forecast/"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {
            "orientation": str(orientation),
            "slope": str(slope),
            "longitude": str(self.lon),
            "latitude": str(self.lat),
            "forecast_days": str(forecast_days),
            "timezone": "utc",
            "required_data": "GHI,DHI,BNI,spec_watts,temp,weather_code"
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            raw_payload = response.json()
            logger.info(f"Successfully retrieved live payload. Intervals: {len(raw_payload.get('values', []))}")
        except Exception as e:
            logger.error(f"Failed to fetch forecast from pvnode API: {e}", exc_info=True)
            return None
        
        try:
            self.storage.initialize_storage()
            tomorrow_date = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%d")

            db_success = self.storage.store_raw_forecast(
                forecast_date=tomorrow_date,
                lat=self.lat,
                lon=self.lon,
                payload=raw_payload
            )
            if db_success:
                logger.info(f"Raw payload successfully cached in database for {tomorrow_date}")
            else:
                logger.warning("Database write indicated failure. Continuing...")
        except Exception as e:
            logger.error(f"Database interaction failed: {e}", exc_info=True)

        logger.info("Parsing raw JSON payload into structured datafram...")
        df_raw = self.interpreter.turn_json_to_dataframe(raw_payload)
        if df_raw.empty:
            logger.error("Interpreter gave an empty dataframe. Aborting...")
            return None
        
        logger.info("Executing pvlib solar physics matrix operations...")
        try:
            calculated_df = self.interpreter.process_solar_metrics(
                df_raw,
                tilt = slope,
                azimuth = orientation
            )
            logger.info("Successfully calculated Plane of Array (POA) and power capacity metrics")
            return calculated_df
        except Exception as e:
            logger.error(f"Physics calculation engine failed: {e}", exc_info=True)
            return None
        