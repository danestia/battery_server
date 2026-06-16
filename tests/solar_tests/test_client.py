import pytest
import requests_mock
from solar_processing.client import PVNodeClient

def test_client_fetch_forecast_success():
    client = PVNodeClient(api_key="mock_key", lat=43.44, lon=-1.55)
    mock_url = "https://api.pvnode.com/v1/forecast/?orientation=180&slope=27&longitude=-1.55&latitude=43.44&forecast_days=1&timezone=utc&required_data=GHI%2CDHI%2CBNI%2Cspec_watts%2Ctemp%2Cweather_code"

    expected_payload = {"status": "success", "values": []}

    with requests_mock.Mocker() as m:
        m.get(mock_url, json=expected_payload, status_code=200)
        assert client.fetch_forecast() == expected_payload