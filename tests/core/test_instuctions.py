import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_tomorrow_instructions_scales_and_slices_correctly():
    mock_db_percentages = {h: float(h) for h in range(24)}

    with patch("app.main.SolarStorageManager.get_hourly_instructions_for_date") as mock_get:
        mock_get.return_record = None
        mock_get.return_value = mock_db_percentages

        response = client.get("/api/v1/instructions/tomorrow")

        assert response.status_code == 200
        payload = response.json()

        assert len(payload) == 10
        assert "8" in payload
        assert "17" in payload
        assert "7" not in payload
        assert "18" not in payload

        assert payload["8"] == 0.08
        assert payload["15"] == 0.15
        assert payload["17"] == 0.17

def test_get_tomorrow_instructions_handles_missing_data():
    with patch("app.main.SolarStorageManager.get_hourly_instructions_for_date") as mock_get:
        mock_get.return_value = {}

        response = client.get("/api/v1/instructions/tomorrow")

        assert response.status_code == 404
        assert "not been generated yet" in response.json()["detail"]