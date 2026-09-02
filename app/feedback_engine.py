import os
from typing import List, Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session

from solar_processing.storage import SolarStorageManager
from app.db.repositories.logs import LogRepository

class FeedbackEngine:


    def __init__(self, solar_storage: Optional[SolarStorageManager] = None):
        self.heartbeats_per_hour = int(os.environ.get("HEARTBEATS_PER_HOUR", 60))
        self.laptop_wattage = float(os.environ.get("LAPTOP_WATTAGE", 60.0))

        self.working_hours = range(8, 18)
        self.working_hours_count = len(self.working_hours)  # 10

        self.solar_storage = solar_storage if solar_storage is not None else SolarStorageManager()


    @staticmethod
    def _to_percentage(value: float) -> float:
        return value if value > 1.0 else value * 100.0
    

    @staticmethod
    def _to_ratio(value: float) -> float:
        return value / 100.0 if value > 1.0 else value
    

    def get_team_hourly_alignment(self, db: Session, target_date: date, target_hour: int) -> float:
        if target_hour not in self.working_hours:
            return 0.0

        date_str = target_date.strftime("%Y-%m-%d")

        solar_map = self.solar_storage.get_hourly_instructions_for_date(date_str) or {}
        hour_weight = solar_map.get(target_hour, 0.0)

        all_counts = LogRepository.get_hourly_charging_counts_for_date(db, date_str)
        hour_has_activity = any(item[1] == target_hour for item in all_counts)

        if not hour_has_activity:
            return 0.0

        return round(self._to_percentage(hour_weight), 1)



    def calculate_daily_individual_feedback(self, db: Session, target_date: date) -> Dict[str, Any]:
        date_str = target_date.strftime("%Y-%m-%d")
        full_solar_map = self.solar_storage.get_hourly_instructions_for_date(date_str) or {}

        # Aggregate solar metrics across working hours
        solar_pcts: List[float] = []
        solar_ratios: List[float] = []
        solar_map: Dict[int, float] = {}

        for h in self.working_hours:
            raw_val = full_solar_map.get(h, 0.0)
            solar_map[h] = raw_val
            solar_pcts.append(self._to_percentage(raw_val))
            solar_ratios.append(self._to_ratio(raw_val))

        max_solar_pct = round(max(solar_pcts), 1) if solar_pcts else 0.0
        min_solar_pct = round(min(solar_pcts), 1) if solar_pcts else 0.0
        avg_solar_pct = round(sum(solar_pcts) / self.working_hours_count, 1)

        max_possible_solar_wh = round(sum(solar_ratios) * self.laptop_wattage, 1)

        raw_logs = LogRepository.get_hourly_charging_counts_for_date(db, date_str)
        profiles: Dict[str, Dict[str, float]] = {}

        for device_id, hour_index, count in raw_logs:
            if hour_index not in self.working_hours:
                continue

            if device_id not in profiles:
                profiles[device_id] = {
                    "total_wh": 0.0,
                    "solar_wh": 0.0,
                    "active_charging_hours": 0.0
                }

            hours_spent_charging = count / self.heartbeats_per_hour
            calculated_wh = hours_spent_charging * self.laptop_wattage
            solar_ratio = self._to_ratio(solar_map.get(hour_index, 0.0))

            profiles[device_id]["total_wh"] += calculated_wh
            profiles[device_id]["solar_wh"] += (calculated_wh * solar_ratio)
            profiles[device_id]["active_charging_hours"] += hours_spent_charging

        device_results = []
        for device_id, metrics in profiles.items():
            total = metrics["total_wh"]
            solar = metrics["solar_wh"]
            other = max(0.0, total - solar)
            alignment_score = (solar / total) * 100.0 if total > 0 else 0.0
            avg_hourly_charging_mins = (metrics["active_charging_hours"] * 60.0) / self.working_hours_count

            feedback_text = (
                f"On {date_str}, your device used {round(solar, 1)} Wh of green solar energy out of a possible "
                f"{max_possible_solar_wh} Wh. The mean hourly solar availability was {avg_solar_pct}%, and "
                f"your average hourly charging duration was {round(avg_hourly_charging_mins, 1)} minutes."
            )

            device_results.append({
                "device_id": device_id,
                "total_energy_wh": round(total, 1),
                "solar_energy_wh": round(solar, 1),
                "other_energy_wh": round(other, 1),
                "alignment_score_pct": round(alignment_score, 1),
                "user_avg_hourly_charging_mins": round(avg_hourly_charging_mins, 1),
                "feedback_text": feedback_text
            })

        return {
            "date": date_str,
            "solar_summary": {
                "max_solar_pct": max_solar_pct,
                "min_solar_pct": min_solar_pct,
                "avg_solar_pct": avg_solar_pct,
                "max_possible_solar_wh_per_device": max_possible_solar_wh,
            },
            "devices": device_results
        }