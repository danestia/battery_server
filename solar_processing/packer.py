import pandas as pd
import logging

logger = logging.getLogger(__name__)


class PiInstructionPacker:

    @staticmethod
    def to_hourly_payload(power_df: pd.DataFrame) -> dict[int, float]:
        if power_df.empty or 'power_percentage' not in power_df.columns:
            logger.warning(
                "Empty DataFrame or missing power_percentage column passed"
            )
            return {}
        
        hourly_series = power_df['power_percentage'].resample('1h').mean()

        payload = {h: 0.0 for h in range(24)}

        for ts, val in hourly_series.items():
            if pd.notna(val):
                decimal_val = float(val) / 100.0
                payload[int(ts.hour)] = round(max(0.0, min(1.0, decimal_val)), 3)

        return payload
    
    @staticmethod
    def slice_working_hours(payload: dict[int, float]) -> dict[int, float]:
        if not payload:
            return {h: 0.0 for h in range(8, 18)}
        
        return {h: payload.get(h, 0.0) for h in range(8, 18)}

    @staticmethod
    def to_protocol_string(
        working_payload: dict[int, float], command: str = "play"
    ) -> str:
        formatted_values = [
            f"{working_payload.get(h, 0.0):.3f}" for h in range(8,18)
        ]
        values_str = "|".join(formatted_values)
        return f"<plantform|update|{values_str}|{command}>"

    @staticmethod
    def to_json_instruction(
        working_payload: dict[int, float], action: str = "update", command: str = "play"
    ) -> dict:
        schedule = {
            str(h): round(val, 3)
            for h, val in working_payload.items()
        }
        return {
            "device": "plantform",
            "action": action,
            "command": command,
            "schedule": schedule,
        }