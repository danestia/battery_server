from datetime import datetime, date, UTC
import mysql.connector
from mysql.connector import Error
from solar_processing.storage import SolarStorageManager

class FeedbackEngine:
    def __init__(self):
        self.storage = SolarStorageManager()

    def get_team_hourly_alignment(self, target_date: date, target_hour: int) -> float:
        query_logs = """
            SELECT plugged
            FROM battery_logs
            WHERE DATE(timestamp) = %s AND HOUR(timestamp) = %s;
        """

        query_weight = """
            SELECT charge_level_pct
            FROM pi_hourly_instructions
            WHERE target_date = %s AND hour_index = %s;
        """

        conn = None
        try:
            conn = self.storage._get_connection()
            cursor = conn.cursor()

            cursor.execute(query_weight, (target_date, target_hour))
            weight_row = cursor.fetchone()
            solar_weight = float(weight_row[0]) / 100.0 if weight_row else 0.0

            cursor.execute(query_logs, (target_date, target_hour))
            logs = cursor.fetchall()

            if not logs:
                return 0.0
            
            total_plugged_minutes = sum(1 for (plugged,) in logs if plugged)
            total_active_minutes = len(logs)

            if total_plugged_minutes == 0:
                return 0.0
            
            team_hour_score = solar_weight * 100.0
            return round(team_hour_score, 1)
        
        except Error as e:
            print(f"[ENGINE ERROR] Failed to calculate EnergySHAPE metrics: {e}")
            return 0.0
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def calculate_daily_individual_feedback(self, target_date: date) -> list[dict]:
        """
        """
        # Assumes a baseline 60W draw rate, meaning 1 log minute plugged = 1 Wh consumed
        query = """
            WITH HourlyDeviceActivity AS (
                SELECT 
                    device_id,
                    HOUR(timestamp) as log_hour,
                    COUNT(*) as total_minutes_plugged
                FROM battery_logs
                WHERE plugged = 1 AND DATE(timestamp) = %s
                GROUP BY device_id, HOUR(timestamp)
            ),
            HourlyWeights AS (
                SELECT 
                    hour_index,
                    (charge_target_pct / 100.0) as solar_ratio
                FROM pi_hourly_instructions
                WHERE target_date = %s
            )
            SELECT 
                da.device_id,
                SUM(da.total_minutes_plugged) as total_wh,
                SUM(da.total_minutes_plugged * hw.solar_ratio) as solar_wh,
                SUM(da.total_minutes_plugged * (1.0 - hw.solar_ratio)) as other_wh
            FROM HourlyDeviceActivity da
            JOIN HourlyWeights hw ON da.log_hour = hw.hour_index
            GROUP BY da.device_id;
        """

        conn = None
        results = []
        try:
            conn = self.storage._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (target_date, target_date))
            rows = cursor.fetchall()

            for row in rows:
                total = float(row['total_wh'])
                solar = float(row['solar_wh'])

                alignment_score = (solar / total) * 100.0 if total > 0 else 0.0

                results.append({
                    "device_id": row['device_id'],
                    "total_energy_wh": round(total, 1),
                    "solar_energy_wh": round(solar, 1),
                    "other_energy_wh": round(row['other_wh'], 1),
                    "alignment_score_pct": round(alignment_score, 1)
                })
            return results
        except Error as e:
            print(f"[ENGINE ERROR] Failed to compile daily report profiles: {e}")
            return []
        finally:
            if conn and conn.is_connected:
                cursor.close()
                conn.close()