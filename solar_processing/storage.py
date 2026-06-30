import os
import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime

class SolarStorageManager:
    
    def __init__(self):
        self.host = os.environ.get("MYSQL_HOST", "localhost")
        self.user = os.environ.get("MYSQL_USER", "root")
        self.password = os.environ.get("MYSQL_PASSWORD", "")
        self.database = os.environ.get("MYSQL_DATABASE", "battery_tracker_hub")

    def _get_connection(self):
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )

    def initialize_storage(self):
        query = """
        CREATE TABLE IF NOT EXISTS pvnode_raw_forecasts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            forecast_date DATE NOT NULL UNIQUE,
            latitude DECIMAL(10, 8) NOT NULL,
            longitude DECIMAL(11, 8) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            raw_payload JSON NOT NULL
        );
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            print("[STORAGE] Ingestion table verified successfully.")
        except Error as e:
            print(f"[STORAGE ERROR] Database initialization failed: {e}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def store_raw_forecast(self, forecast_date: str, lat: float, lon: float, payload: dict) -> bool:
        query = """
        INSERT INTO pvnode_raw_forecasts (forecast_date, latitude, longitude, raw_payload)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            latitude = VALUES(latitude),
            longitude = VALUES(longitude),
            raw_payload = VALUES(raw_payload);
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            json_str = json.dumps(payload)
            
            cursor.execute(query, (forecast_date, lat, lon, json_str))
            conn.commit()
            print(f"[STORAGE] Safely saved raw JSON for {forecast_date} in MySQL.")
            return True
            
        except Error as e:
            print(f"[STORAGE ERROR] Failed to save raw payload to MySQL: {e}")
            return False
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def retrieve_raw_forecast(self, forecast_date: str) -> dict:
        
        query = "SELECT raw_payload FROM pvnode_raw_forecasts WHERE forecast_date = %s"
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (forecast_date,))
            row = cursor.fetchone()
            
            if row:
                return json.loads(row[0])
            return None
            
        except Error as e:
            print(f"[STORAGE ERROR] Failed to retrieve payload: {e}")
            return None
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()