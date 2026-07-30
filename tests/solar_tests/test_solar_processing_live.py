import sys
import os
import unittest
import requests
import pandas as pd

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from solar_processing.interpreter import SolarDataInterpreter
from solar_processing.packer import PiInstructionPacker

def load_env_from_root():
    
    dotenv_path = os.path.join(project_root, ".env")
    if os.path.exists(dotenv_path):
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    clean_key = key.strip()
                    clean_value = value.strip().strip("'\"")
                    os.environ[clean_key] = clean_value
    else:
        print(f"[WARNING] .env file not found at: {dotenv_path}")

load_env_from_root()

class TestSolarProcessingLive(unittest.TestCase):

    def setUp(self):
        # Coordinates and orientation details for ESTIA 2 solar panels
        self.latitude = "43.44608207499594"
        self.longitude = "-1.5526873172625033"
        self.orientation = "180"
        self.slope = "27"
        self.forecast_days = "1"
        self.timezone = "utc"
        self.required_data = "GHI,DHI,BNI,spec_watts,temp,weather_code"
        
        self.api_key = os.environ.get("PVNODE_API_KEY")
        self.endpoint = "https://api.pvnode.com/v1/forecast/"

    def test_live_pipeline_execution(self):
        self.assertTrue(
            self.api_key, 
            "PVNODE_API_KEY was not found in your environment or project root .env file."
        )
        
        print("\n[LIVE TEST] Initiating real API call to pvnode...")
        
        params = {
            "orientation": self.orientation,
            "slope": self.slope,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "forecast_days": self.forecast_days,
            "timezone": self.timezone,
            "required_data": self.required_data
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            response = requests.get(self.endpoint, headers=headers, params=params, timeout=15)
            self.assertEqual(
                response.status_code, 200, 
                f"API call failed with status code {response.status_code}: {response.text}"
            )
            print("[LIVE TEST] Successfully connected and authenticated with pvnode API.")
            
            payload_json = response.json()
            self.assertIn("values", payload_json, "Payload did not contain expected 'values' array.")
            self.assertTrue(len(payload_json["values"]) > 0, "The 'values' array returned by the API is empty.")
            print(f"[LIVE TEST] Received {len(payload_json['values'])} raw data points.")

        except requests.exceptions.RequestException as e:
            self.fail(f"Network request to pvnode failed: {e}")

        print("[LIVE TEST] Pushing live payload to SolarDataInterpreter...")
        interpreter = SolarDataInterpreter(lat=float(self.latitude), lon=float(self.longitude))
        
        df_raw = interpreter.turn_json_to_dataframe(payload_json)
        self.assertFalse(df_raw.empty, "Interpreter parsed an empty DataFrame.")
        self.assertIn("GHI", df_raw.columns, "DataFrame is missing expected GHI column.")
        
        df_daily = df_raw.iloc[:96, :]
        self.assertEqual(len(df_daily), 96, f"Expected 96 interval records, got {len(df_daily)}")

        calculated_df = interpreter.process_solar_metrics(
            df_daily, 
            tilt=float(self.slope), 
            azimuth=float(self.orientation)
        )
        
        self.assertIn("power_percentage", calculated_df.columns, "Metrics calculator missed 'power_percentage'.")
        self.assertIn("POA", calculated_df.columns, "Metrics calculator missed Plane of Array (POA) irradiance.")
        print("[LIVE TEST] Physics calculations executed successfully via pvlib.")

        print("[LIVE TEST] Packing calculated outputs into hourly instructions...")
        hourly_instructions = PiInstructionPacker.to_hourly_payload(calculated_df)
        
        self.assertIsInstance(hourly_instructions, dict, "Instruction payload must be a dictionary.")
        self.assertEqual(len(hourly_instructions), 24, f"Expected exactly 24 hourly values, got {len(hourly_instructions)}")
        
        for hour, value in hourly_instructions.items():
            self.assertTrue(0.0 <= value <= 100.0, f"Value for hour {hour} ({value}%) is out of bounds (0-100%).")

        print("[LIVE TEST] Hourly instructions successfully packed and validated!")
        print("\n=== COMPILED LIVE INSTR_PAYLOAD ===")
        for hr in sorted(hourly_instructions.keys()):
            print(f"Hour {hr:02d}:00  -->  {hourly_instructions[hr]:.1f}% Max Capacity")
        print("===================================\n")

if __name__ == "__main__":
    unittest.main()
