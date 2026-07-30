import pandas as pd
import logging
from pvlib import location, irradiance, temperature, pvsystem

logger = logging.getLogger(__name__)

class SolarDataInterpreter:
    def __init__(self, lat: float = 43.446082, lon: float = -1.552687, tz: str = 'UTC'):
        self.site = location.Location(lat, lon, tz=tz)

    def turn_json_to_dataframe(self, json_data: dict) -> pd.DataFrame:
        if not json_data or 'values' not in json_data:
            logger.warning("Empty or malformed JSON payload received from solar API")
            return pd.DataFrame()
        try:
            df = pd.DataFrame(json_data['values'])
            if df.empty:
                return df
            
            required_cols = ['dtm', 'GHI', 'DHI', 'BNI', 'temp']
            for col in required_cols:
                if col not in df.columns:
                    raise KeyError(f"Missing essential telemetry metric column: {col}")
                
            df['dtm'] = pd.to_datetime(df['dtm'])
            df = df.set_index('dtm')

            if 'spec_watts' not in df.columns:
                df['spec_watts'] = 0.0

            for col in ['GHI', 'DHI', 'BNI', 'temp', 'spec_watts']:
                df[col] = df[col].astype(float)

            return df[['GHI', 'DHI', 'BNI', 'temp', 'spec_watts']]

        except Exception as e:
            logger.error(f"Failed to parse live JSON structure into Dataframe: {e}")
            return pd.DataFrame()

    def process_solar_metrics(self, df: pd.DataFrame, tilt: float, azimuth: float) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        
        try:
            times = df.index
            solar_pos = self.site.get_solarposition(times=times)

            poa = irradiance.get_total_irradiance(
                surface_tilt=tilt,
                surface_azimuth=azimuth,
                dni=df['BNI'], ghi=df['GHI'], dhi=df['DHI'],
                solar_zenith=solar_pos['apparent_zenith'],
                solar_azimuth=solar_pos['azimuth']
            )

            processed = pd.DataFrame({
                'POA': poa['poa_global'].fillna(0.0),
                'air_temp': df['temp']
            }, index=times)

            processed['POA'] = processed['POA'].clip(lower=0.0)

            cell_temps = []
            for _, r in processed.iterrows():
                c_temp = temperature.pvsyst_cell(poa_global=r['POA'], temp_air=r['air_temp'])
                cell_temps.append(c_temp)
            processed['cell_temp'] = cell_temps        

            pdc0 = 1000.0
            gamma_pdc = -0.004
            powers = []
            for _, row in processed.iterrows():
                p_dc = pvsystem.pvwatts_dc(
                    effective_irradiance=row['POA'], 
                    temp_cell=row['cell_temp'], 
                    pdc0=pdc0, 
                    gamma_pdc=gamma_pdc
                )
                powers.append(p_dc)

            processed['power_dc'] = powers
            processed['power_dc'] = processed['power_dc'].fillna(0.0).clip(lower=0.0)

            max_power = processed['power_dc'].max()
            processed['power_percentage'] = (processed['power_dc'] / max_power * 100) if max_power > 0 else 0.0
            return processed
        
        except Exception as e:
            logger.error(f"Mathematical runtime exception during pvlib translation: {e}")
            return pd.DataFrame()