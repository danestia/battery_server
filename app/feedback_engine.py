from datetime import datetime, date, UTC
import mysql.connector
from mysql.connector import Error
from solar_processing.storage import SolarStorageManager
import os
from sqlalchemy.orm import Session
from app.db.repositories.logs import LogRepository

class FeedbackEngine:
    def __init__(self):

        self.heartbeats_per_hour = int(os.environ.get("HEARTBEATS_PER_HOUR", 60))
        self.laptop_wattage = 60.0
        self.solar_storage = SolarStorageManager()

    def get_team_hourly_alignment(self, db: Session, target_date: date, target_hour: int) -> float:
        date_str = target_date.strftime("%Y-%m-%d")

        solar_map = self.solar_storage.get_hourly_instructions_for_date(date_str)
        hour_weight = solar_map.get(target_hour, 0.0)

        all_counts = LogRepository.get_hourly_charging_counts_for_date(db, date_str)

        hour_has_activity = any(item[1] == target_hour for item in all_counts)

        if not hour_has_activity:
            return 0.0
        
        return round(hour_weight, 1)

    def calculate_daily_individual_feedback(self, db: Session, target_date: date) -> list[dict]:
        date_str = target_date.strftime("%Y-%m-%d")
        solar_map = self.solar_storage.get_hourly_instructions_for_date(date_str)

        raw_logs = LogRepository.get_hourly_charging_counts_for_date(db, date_str)

        profiles = {}

        for device_id, hour_index, count in raw_logs:
            if device_id not in profiles:
                profiles[device_id] = {"total_wh": 0.0, "solar_wh": 0.0}

            hours_spent_charging = count / self.heartbeats_per_hour
            calculated_wh = hours_spent_charging * self.laptop_wattage

            solar_ratio = solar_map.get(hour_index, 0.0) / 100.0

            profiles[device_id]["total_wh"] += calculated_wh
            profiles[device_id]["solar_wh"] += (calculated_wh * solar_ratio)

        results = []
        for device_id, metrics in profiles.items():
            total = metrics["total_wh"]
            solar = metrics["solar_wh"]
            other = total - solar
            alignment_score = (solar / total) * 100.0 if total > 0 else 0.0

            results.append({
                "device_id": device_id,
                "total_energy_wh": round(total, 1),
                "solar_energy_wh": round(solar, 1),
                "other_energy_wh": round(other, 1),
                "alignment_score_pct": round(alignment_score, 1)
            })

        return results
