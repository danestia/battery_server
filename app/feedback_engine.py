import os
from typing import List, Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session

from solar_processing.storage import SolarStorageManager
from app.db.repositories.logs import LogRepository

class FeedbackEngine:


    def __init__(self, solar_storage: Optional[SolarStorageManager] = None) -> None:
        self.heartbeats_per_hour = int(os.environ.get("HEARTBEATS_PER_HOUR", 60))

        start_hour = int(os.environ.get("WORKING_HOUR_START", 8))
        end_hour = int(os.environ.get("WORKING_HOUR_END", 18))
        self.working_hours = range(start_hour, end_hour)
        self.working_hours_count = len(self.working_hours)  # 10

        self.solar_storage = (
            solar_storage if solar_storage is not None else SolarStorageManager()
        )
    

    @staticmethod
    def _to_ratio(value: float) -> float:
        return value / 100.0 if value > 1.0 else value


    def calculate_daily_individual_feedback(self, db: Session, target_date: date) -> Dict[str, Any]:
        date_str = target_date.strftime("%Y-%m-%d")
        full_solar_map = (
            self.solar_storage.get_hourly_instructions_for_date(date_str) or {}
        )

        solar_weights: Dict[int, float] = {}

        for h in self.working_hours:
            solar_weights[h] = self._to_ratio(full_solar_map.get(h, 0.0))            

        max_possible_points = sum(
            max(w, 1.0 - w) for w in solar_weights.values()
        )

        raw_logs = LogRepository.get_hourly_charging_counts_for_date(db, date_str)

        device_hourly_counts: Dict[str, Dict[int, int]] = {}

        for device_id, hour_index, count in raw_logs:
            if hour_index in self.working_hours:
                if device_id not in device_hourly_counts:
                    device_hourly_counts[device_id] = {}
                device_hourly_counts[device_id][hour_index] = count

        device_results: List[Dict[str, Any]] = []

        for device_id, hour_counts in device_hourly_counts.items():
            total_earned_points = 0.0
            positive_points = 0.0
            negative_points = 0.0
            good_action_hours = 0
            bad_action_hours = 0
            total_plugged_hours = 0.0

            for h in self.working_hours:
                count =  hour_counts.get(h, 0)
                plugged_ratio = min(1.0, count / self.heartbeats_per_hour)
                unplugged_ratio = 1.0 - plugged_ratio
                total_plugged_hours += plugged_ratio

                w_h = solar_weights[h]

                hour_points = (
                    (plugged_ratio * w_h)
                    - (plugged_ratio * (1.0 - w_h))
                    + (unplugged_ratio * (1.0 - w_h))
                    - (unplugged_ratio * w_h)
                )

                total_earned_points += hour_points

                if hour_points >= 0:
                    positive_points += hour_points
                    good_action_hours += 1
                else:
                    negative_points += abs(hour_points)
                    bad_action_hours += 1

            if max_possible_points > 0:
                normalized_score = (
                    (total_earned_points + max_possible_points)
                    / (2.0 * max_possible_points)
                ) * 100.0
            else:
                normalized_score = 50.0

            feedback_text = (
                f"Date: {date_str}, Score: {round(normalized_score, 1)}%. "
            )

            device_results.append(
                {
                    "device_id": device_id,
                    "score_pct": round(normalized_score, 1),
                    "net_points_earned": round(total_earned_points, 2),
                    "positive_points": round(positive_points, 2),
                    "negative_points": round(negative_points, 2),
                    "good_action_hours": good_action_hours,
                    "bad_action_hours": bad_action_hours,
                    "total_plugged_hours": round(total_plugged_hours, 1),
                    "feedback_text": feedback_text,
                }
            )
            

        return {
            "date": date_str,
            "max_possible_day_points": round(max_possible_points, 2),
            "devices": device_results,
        }