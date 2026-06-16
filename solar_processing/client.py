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

    def fetch_forecast(self, orientation: str = '180', slope: str = '27', days: str = '1', tz: str = 'utc') -> dict:
        required_data = 'GHI%2CDHI%2CBNI%2Cspec_watts%2Ctemp%2Cweather_code'
        url = (f"{self.base_url}?orientation={orientation}&slope={slope}"
               f"&longitude={self.lon}&latitude={self.lat}"
               f"&forecast_days={days}&timezone={tz}&required_data={required_data}")
        
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"PVNode API request failed: {e}")
            raise RuntimeError(f"Failed to fetch live solar forecast metrics: {e}")
    

