import os
import logging
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv

from solar_processing.client import PVNodeClient
from solar_processing.interpreter import SolarDataInterpreter
from solar_processing.packer import PiInstructionPacker
from solar_processing.storage import SolarStorageManager

load_dotenv()
logger = logging.getLogger(__name__)

class SolarOrchestrator:
    def __init__(
        self,
        api_key: str,
        lat: float,
        lon: float,
        tilt: float = 27.0,
        azimuth: float = 180.0,
    ):
        self.lat = lat
        self.lon = lon
        self.tilt = tilt
        self.azimuth = azimuth
        
        self.client = PVNodeClient(api_key, lat, lon)
        self.interpreter = SolarDataInterpreter(lat, lon)
        self.packer = PiInstructionPacker()
        self.storage = SolarStorageManager()

    def run_daily_pipeline(self) -> dict[int, float]:
        try:
            logger.info("Initiating solar processing daily sync...")
            self.storage.initialize_storage()

            raw_json = self.client.fetch_forecast(
                orientation=str(int(self.azimuth)), 
                slope=str(int(self.tilt)),
                days='1',
            )
            
            tomorrow_date = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%d")

            self.storage.store_raw_forecast(tomorrow_date, self.lat, self.lon, raw_json)

            base_df = self.interpreter.turn_json_to_dataframe(raw_json)
            if base_df.empty:
                raise ValueError("Parsed data frame is empty. Pipeine aborted.")
            
            calculated_df = self.interpreter.process_solar_metrics(
                base_df, self.tilt, self.azimuth
            )
            final_payload = self.packer.to_hourly_payload(calculated_df)

            self.storage.store_hourly_instructions(tomorrow_date, final_payload)

            logger.info("Solar tracking engine successfully compiled instructions.")

            return final_payload
        
        except Exception as e:
            logger.error(f"Critical failure inside Solar Processing Orchestration Chain: {e}")
            return {h: 0.0 for h in range(24)}
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    API_KEY = os.getenv("PVNODE_API_KEY")
    LAT = float(os.getenv("SOLAR_LAT", "43.446082"))
    LON = float(os.getenv("SOLAR_LON", "-1.552687"))
    TILT = float(os.getenv("PANEL_TILT", "27.0"))
    AZIMUTH = float(os.getenv("PANEL_AZIMUTH", "180.0"))

    if not API_KEY:
        raise ValueError("Missing PVNODE API_KEY in environment variables")
    
    orchestrator = SolarOrchestrator(API_KEY, lat=LAT, lon=LON, tilt=TILT, azimuth=AZIMUTH)
    print("Run result:", orchestrator.run_daily_pipeline())
