import pytest
from unittest.mock import MagicMock, patch
from datetime import date
from app.feedback_engine import FeedbackEngine

@pytest.fixture
def feedback_engine():
    engine = FeedbackEngine()
    engine.heartbeats_per_hour = 60
    engine.laptop_wattage = 60.0
    return engine

@patch("app.feedback_engine.LogRepository.get_hourly_charging_counts_for_date")
@patch("app.feedback_engine.SolarStorageManager.get_hourly_instructions_for_date")
def test_get_team_hourly_alignment_active(mock_get_instructions, mock_get_logs, feedback_engine):
    
    mock_db_session = MagicMock()
    target_date = date(2026, 7, 16)

    mock_get_instructions.return_value = {12: 50.0}

    mock_get_logs.return_value = [("device_A", 12, 30)]

    score = feedback_engine.get_team_hourly_alignment(mock_db_session, target_date, 12)

    assert score == 50.0

@patch("app.feedback_engine.LogRepository.get_hourly_charging_counts_for_date")
@patch("app.feedback_engine.SolarStorageManager.get_hourly_instructions_for_date")
def test_get_team_hourly_alignmnet_inactive(mock_get_instructions, mock_get_logs, feedback_engine):

    mock_db_session = MagicMock()
    target_date = date(2026, 7, 16)

    mock_get_instructions.return_value = {12: 50.0}

    mock_get_logs.return_value = []

    score = feedback_engine.get_team_hourly_alignment(mock_db_session, target_date, 12)

    assert score == 0

@patch("app.feedback_engine.LogRepository.get_hourly_charging_counts_for_date")
@patch("app.feedback_engine.SolarStorageManager.get_hourly_instructions_for_date")
def test_calculate_daily_individual_feedback(mock_get_instructions, mock_get_logs, feedback_engine):
    """
    Test individual device calculations.
    For device_A: 
      - Charges in hour 10 for 30 heartbeats. Solar target is 100.0%.
      - Charges in hour 11 for 30 heartbeats. Solar target is 50.0%.
    Math:
      - Hour 10: 30 / 60 = 0.5 hours. 0.5 * 60W = 30.0 Wh. Solar component = 30.0 * 1.0 = 30.0 Wh.
      - Hour 11: 30 / 60 = 0.5 hours. 0.5 * 60W = 30.0 Wh. Solar component = 30.0 * 0.5 = 15.0 Wh.
      - Total Wh: 60.0 Wh.
      - Total Solar Wh: 45.0 Wh.
      - Alignment: (45.0 / 60.0) * 100 = 75.0%
    """
    mock_db_session = MagicMock()
    target_date = date(2026, 7, 16)

    mock_get_instructions.return_value = {10: 100.0, 11: 50.0}

    mock_get_logs.return_value = [
        ("device_A", 10, 30),
        ("device_A", 11, 30)
    ]

    results = feedback_engine.calculate_daily_individual_feedback(mock_db_session, target_date)

    assert len(results["devices"]) == 1
    device_res = results["devices"][0]

    assert device_res["device_id"] == "device_A"
    assert device_res["total_energy_wh"] == 60.0
    assert device_res["solar_energy_wh"] == 45.0
    assert device_res["other_energy_wh"] == 15.0
    assert device_res["alignment_score_pct"] == 75.0