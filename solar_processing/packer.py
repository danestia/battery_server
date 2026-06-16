import pandas as pd

class PiInstructionPacker:
    #packages floating-point timelines for easier reading by Raspberry Pi
    @staticmethod
    def to_hourly_payload(power_df: pd.DataFrame) -> dict:
        if power_df.empty or 'power_percentage' not in power_df.columns:
            return {}
        
        hourly_series = power_df['power_percentage'].resample('1h').mean()

        payload = {h: 0.0 for h in range(24)}

        for ts, val in hourly_series.items():
            if pd.notna(val):
                payload[int(ts.hour)] = round(float(val), 2)

        return payload