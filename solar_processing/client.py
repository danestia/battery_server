import requests
import logging

logger = logging.getLogger(__name__)

class PVNodeClient:

    def __init__(self, api_key: str, lat: float, lon: float):
        if not api_key:
            raise ValueError("API key cannot be empty or None")
        self.api_key = api_key
        self.lat = lat
        self.lon = lon
        self.base_url = "https://api.pvnode.com/v1/forecast/"

    def fetch_forecast(
            self,
            orientation: str = '180',
            slope: str = '27',
            days: str = '1',
            tz: str = 'utc',
        ) -> dict:
            params = {
                 "orientation": str(orientation),
                 "slope": str(slope),
                 "longitude": self.lon,
                 "latitude": self.lat,
                 "forecast_days": str(days),
                 "timezone": tz,
                 "required_data": "GHI,DHI,BNI,spec_watts,temp,weather_code",
            }
            headers = {"Authorization": f"Bearer {self.api_key}"}

            try:
                 response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
                 response.raise_for_status()
                 return response.json()
            except requests.exceptions.RequestException as e:
                 logger.error(f"PVNode API request failed: {e}")
                 raise RuntimeError(f"Failed to fetch live solar forecast metrics: {e}")

