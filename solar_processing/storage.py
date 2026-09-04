import json
import logging
import os
from typing import Any, Dict, Optional

import mysql.connector
from mysql.connector import Error

logger = logging.getLogger(__name__)


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
            database=self.database,
        )

    def initialize_storage(self) -> None:
        """Initializes raw forecast and hourly instruction storage tables in MySQL if missing."""
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
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query_raw)
            cursor.execute(query_instructions)
            conn.commit()
            logger.info("Ingestion and instruction tables verified successfully.")
        except Error as e:
            logger.error(f"Database initialization failed: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def store_raw_forecast(
        self, forecast_date: str, lat: float, lon: float, payload: dict
    ) -> bool:
        """Stores or updates the raw solar forecast JSON payload for a target date."""
        query = """
        INSERT INTO pvnode_raw_forecasts (forecast_date, latitude, longitude, raw_payload)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            latitude = VALUES(latitude),
            longitude = VALUES(longitude),
            raw_payload = VALUES(raw_payload);
        """
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            json_str = json.dumps(payload)
            cursor.execute(query, (forecast_date, lat, lon, json_str))
            conn.commit()
            logger.info(f"Safely saved raw JSON for {forecast_date} in MySQL.")
            return True
        except Error as e:
            logger.error(f"Failed to save raw payload to MySQL: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def store_hourly_instructions(
        self, target_date: str, hourly_map: Dict[int, float]
    ) -> bool:
        """Stores or updates normalized hourly charge targets (0.0..1.0) into percentage values (0..100%)."""
        query = """
        INSERT INTO pi_hourly_instructions (target_date, hour_index, charge_target_pct)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE charge_target_pct = VALUES(charge_target_pct);
        """
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            data_tuples = [
                (target_date, hour, round(pct * 100.0, 2))
                for hour, pct in hourly_map.items()
            ]
            cursor.executemany(query, data_tuples)
            conn.commit()
            logger.info(
                f"Actionable hourly instructions saved for date: {target_date}"
            )
            return True
        except Error as e:
            logger.error(f"Failed to save hourly instructions: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def retrieve_raw_forecast(self, forecast_date: str) -> Optional[Dict[str, Any]]:
        """Retrieves raw forecast JSON for a specific date."""
        query = "SELECT raw_payload FROM pvnode_raw_forecasts WHERE forecast_date = %s"
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (forecast_date,))
            row = cursor.fetchone()

            if row and row[0]:
                return json.loads(row[0]) if isinstance(row[0], str) else row[0]
            return None
        except Error as e:
            logger.error(f"Failed to retrieve raw payload: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def get_hourly_instructions_for_date(self, target_date: str) -> Dict[int, float]:
        """Retrieves stored hourly instructions for a date as {hour_index: percentage}."""
        query = "SELECT hour_index, charge_target_pct FROM pi_hourly_instructions WHERE target_date = %s"
        hourly_map = {}
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (target_date,))
            rows = cursor.fetchall()

            for hour, pct in rows:
                hourly_map[int(hour)] = float(pct)

            return hourly_map
        except Error as e:
            logger.error(f"Failed to retrieve hourly instructions: {e}")
            return {}
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()