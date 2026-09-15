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
    def slice_working_hours(payload: dict[int, float]) -> list[float]:
        if not payload:
            return [0.0 for _ in range(8, 18)]
        
        return [round(payload.get(h, 0.0), 3) for h in range (8, 18)]

    @staticmethod
    def to_protocol_string(
        working_payload: list[float], command: str = "play"
    ) -> str:
        formatted_values = [
            f"{val:.3f}" for val in working_payload
        ]
        values_str = "|".join(formatted_values)
        return f"<plantform|update|{values_str}|{command}>"

    @staticmethod
    def to_json_instruction(
        working_payload: list[float], action: str = "update", command: str = "play"
    ) -> dict:
        schedule = [f"{float(val):.3f}" for val in working_payload]        
        return {
            "type": "action",
            "device": "plantform1",
            "command": f"{action}-{command}",
            "params": schedule,
        }