import os
import mysql.connector
from mysql.connector import Error
import json

class SolarStorageManager:
    
    def __init__(self):
        self.host = os.environ.get("MYSQL_HOST", "localhost")
        self.user = os.environ.get("MYSQL_USER", "root")
        self.password = os.environ.get("MYSQL_PASSWORD", "")
        self.database = os.environ.get("MYSQL_DATABASE", "battery_tracker")

    def _get_connection(self):
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )

    def initialize_storage(self):
        query_raw = """
        CREATE TABLE IF NOT EXISTS pvnode_raw_forecasts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            forecast_date DATE NOT NULL UNIQUE,
            latitude DECIMAL(10, 8) NOT NULL,
            longitude DECIMAL(11, 8) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            raw_payload JSON NOT NULL
        );
        """

        query_instructions = """
        CREATE TABLE IF NOT EXISTS pi_hourly_instructions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            target_date DATE NOT NULL,
            hour_index INT NOT NULL,
            charge_target_pct DECIMAL(5,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_date_hour (target_date, hour_index)
        );
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query_raw)
            cursor.execute(query_instructions)
            conn.commit()
            print("[STORAGE] Ingestion and instruction tables verified successfully.")
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

    def store_hourly_instructions(self, target_date: str, hourly_map: dict) -> bool:
        query = """
        INSERT INTO pi_hourly_instructions (target_date, hour_index, charge_target_pct)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE charge_target_pct = VALUES(charge_target_pct);
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            data_tuples = [(target_date, hour, pct * 100.0) for hour, pct in hourly_map.items()]
            cursor.executemany(query, data_tuples)
            conn.commit()
            print(f"[STORAGE] Actionable hourly instructions saved for {target_date}")
            return True
        except Error as e:
            print(f"[STORAGE ERROR] Failed to save hourly instructions: {e}")
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

    def get_hourly_instructions_for_date(self, target_date: str) -> dict:
        query = "SELECT hour_index, charge_target_pct FROM pi_hourly_instructions WHERE TARGET_DATE = %s"
        hourly_map ={}
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (target_date,))
            rows = cursor.fetchall()

            for hour, pct in rows:
                hourly_map[int(hour)] = float(pct)

            return hourly_map
        except Error as e:
            print(f"[STORAGE ERROR] Failed to retrieve hourly instrucitons: {e}")
            return {}
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()