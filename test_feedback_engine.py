import pytest
from datetime import date
from unittest.mock import MagicMock, patch

from app.feedback_engine import FeedbackEngine

@pytest.fixture
def feedback_engine():
    with patch("app.feedback_engine.SolarStorageManager") as mock_storage_cls:
        engine = FeedbackEngine()
        engine.mock_solar_storage = mock_storage_cls.return_value
        return engine

@pytest.fixture
def mock_db_session():
    return MagicMock()

# Team tests

def test_team_alignment_non_working_hours(feedback_engine, mock_db_session):
    test_date = date(2026, 8, 26)

    for non_working_hour in [0, 7, 18, 23]:
        score = feedback_engine.get_team_hourly_alignment(
            mock_db_session, test_date, target_hour=non_working_hour
        )
        assert score == 0.0

    feedback_engine.mock_solar_storage.get_hourly_instructions_for_date.assert_not_called()


@patch("app.feedback_engine.LogRepository")
def test_team_alignment_zero_activity(mock_log_repo, feedback_engine, mock_db_session):
    test_date = date(2026, 8, 26)
    target_hour = 12

    feedback_engine.mock_solar_storage.get_hourly_instructions_for_date.return_value = {12: 80.0}

    mock_log_repo.get_hourly_charging_counts_for_date.return_value = [
        ("device_1", 9, 60),
    ]

    score = feedback_engine.get_team_hourly_alignment(
        mock_db_session, test_date, target_hour=target_hour
    )

    assert score == 0.0


@patch("app.feedback_engine.LogRepository")
def test_team_alignment_active_hour(mock_log_repo, feedback_engine, mock_db_session):
    test_date = date(2026, 8, 26)
    target_hour = 14

    feedback_engine.mock_solar_storage.get_hourly_instructions_for_date.return_value = {14: 0.75}
    mock_log_repo.get_hourly_charging_counts_for_date.return_value = [
        ("device_1", 14, 60)
    ]

    score = feedback_engine.get_team_hourly_alignment(
        mock_db_session, test_date, target_hour=target_hour
    )

    assert score == 75.0

# Individual tests

@patch("app.feedback_engine.LogRepository")
def test_daily_feedback_zero_activity(mock_log_repo, feedback_engine, mock_db_session):
    test_date = date(2026, 8, 26)

    feedback_engine.mock_solar_storage.get_hourly_instructions_for_date.return_value = {
        h: 50.0 for h in range(8, 18)
    }
    mock_log_repo.get_hourly_charging_counts_for_date.return_value = []

    result = feedback_engine.calculate_daily_individual_feedback(mock_db_session, test_date)

    assert result["date"] == "2026-08-26"
    assert result["solar_summary"]["avg_solar_pct"] == 50.0
    assert result["solar_summary"]["max_possible_solar_wh_per_device"] == 300.0
    assert result["devices"] == []

@patch("app.feedback_engine.LogRepository")
def test_daily_feedback_100_percent_solar_alignment(mock_log_repo, feedback_engine, mock_db_session):
    test_date = date(2026, 8, 26)

    feedback_engine.mock_solar_storage.get_hourly_instructions_for_date.return_value = {
        h: 100.0 for h in range(8,18)
    }

    mock_log_repo.get_hourly_charging_counts_for_date.return_value = [
        ("device_laptop_1", h, 60) for h in range(8,18)
    ]

    result = feedback_engine.calculate_daily_individual_feedback(mock_db_session, test_date)

    assert len(result["devices"]) == 1
    device_data = result["devices"][0]

    assert device_data["device_id"] == "device_laptop_1"
    assert device_data["total_energy_wh"] == 600.0
    assert device_data["solar_energy_wh"] == 600.0
    assert device_data["other_energy_wh"] == 0.0
    assert device_data["alignment_score_pct"] == 100.0
    assert device_data["user_avg_hourly_charging_mins"] == 60.0

@patch("app.feedback_engine.LogRepository")
def test_daily_feedback_filters_non_working_hour_logs(mock_log_repo, feedback_engine, mock_db_session):
    test_date = date(2026, 8, 26)

    feedback_engine.mock_solar_storage.get_hourly_instructions_for_date.return_value = {12: 100}

    mock_log_repo.get_hourly_charging_counts_for_date.return_value = [
        ("device_1", 2, 60),
        ("device_1", 12, 60),
    ]

    result = feedback_engine.calculate_daily_individual_feedback(mock_db_session, test_date)

    assert len(result["devices"]) == 1
    device_data = result["devices"][0]

    assert device_data["total_energy_wh"] == 60.0
    assert device_data["solar_energy_wh"] == 60.0