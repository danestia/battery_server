from datetime import date
from unittest.mock import MagicMock, patch
import pytest

from app.feedback_engine import FeedbackEngine

@pytest.fixture
def mock_solar_storage():
    return MagicMock()

@pytest.fixture
def feedback_engine(mock_solar_storage):
    return FeedbackEngine(solar_storage=mock_solar_storage)

@pytest.fixture
def mock_db_session():
    return MagicMock()

class TestCalculateDailyIndividualFeedback:

    def test_perfect_adherence_high_solar(
        self, feedback_engine, mock_solar_storage, mock_db_session
    ):
        target_date = date(2026, 9, 10)
        date_str = "2026-09-10"

        mock_solar_storage.get_hourly_instructions_for_date.return_value = {
            h: 100.0 for h in range(8, 18)
        }

        mock_logs =[("dev1", h, 60) for h in range(8, 18)]

        with patch(
            "app.feedback_engine.LogRepository.get_hourly_charging_counts_for_date",
            return_value=mock_logs,
        ):
            result = feedback_engine.calculate_daily_individual_feedback(
                mock_db_session, target_date
            )

        assert result["date"] == date_str
        assert result["max_possible_day_points"] == 10.0
        assert len(result["devices"]) == 1

        device_data = result["devices"][0]
        assert device_data["device_id"] == "dev1"
        assert device_data["score_pct"] == 100.0
        assert device_data["net_points_earned"] == 10.0
        assert device_data["positive_points"] == 10.0
        assert device_data["negative_points"] == 0.0
        assert device_data["good_action_hours"] == 10
        assert device_data["bad_action_hours"] == 0
        assert device_data["total_plugged_hours"] == 10.0


    def test_worst_adherence_high_solar(
        self, feedback_engine, mock_solar_storage, mock_db_session
    ):
        target_date = date(2026, 9, 10)

        mock_solar_storage.get_hourly_instructions_for_date.return_value = {
            h: 100.0 for h in range(8, 18)
        }

        mock_logs =[("dev1", 8, 0)]

        with patch(
            "app.feedback_engine.LogRepository.get_hourly_charging_counts_for_date",
            return_value=mock_logs,
        ):
            result = feedback_engine.calculate_daily_individual_feedback(
                mock_db_session, target_date
            )

        device_data = result["devices"][0]
        assert device_data["score_pct"] == 0.0
        assert device_data["net_points_earned"] == -10.0
        assert device_data["negative_points"] == 10.0
        assert device_data["bad_action_hours"] == 10
        assert device_data["total_plugged_hours"] == 0.0

    def test_mixed_behavior_and_partial_charging(
        self, feedback_engine, mock_solar_storage, mock_db_session
    ):
        target_date = date(2026, 9, 10)

        mock_solar_storage.get_hourly_instructions_for_date.return_value = {
            8: 80.0,
            9: 20.0,
        }

        mock_logs = [("dev1", 8, 30)]

        with patch(
            "app.feedback_engine.LogRepository.get_hourly_charging_counts_for_date",
            return_value=mock_logs,
        ):
            result = feedback_engine.calculate_daily_individual_feedback(
                mock_db_session, target_date
            )

        assert result["max_possible_day_points"] == 9.6

        device_data = result["devices"][0]
        assert device_data["net_points_earned"] == 8.6
        assert device_data["total_plugged_hours"] == 0.5


    def test_off_hours_logs_are_filtered_out(
            self, feedback_engine, mock_solar_storage, mock_db_session
    ):
        target_date = date(2026, 9, 10)
        mock_solar_storage.get_hourly_instructions_for_date.return_value = {}

        mock_logs = [("dev1", 2, 60), ("dev1", 23, 60)]

        with patch(
            "app.feedback_engine.LogRepository.get_hourly_charging_counts_for_date",
            return_value=mock_logs,
        ):
            result = feedback_engine.calculate_daily_individual_feedback(
                mock_db_session, target_date
            )

        assert len(result["devices"]) == 0


    def test_multiple_devices_scored_independently(
        self, feedback_engine, mock_solar_storage, mock_db_session
    ):
        target_date = date(2026, 9, 10)
        mock_solar_storage.get_hourly_instructions_for_date.return_value = {
            h: 100.0 for h in range(8, 18)
        }

        mock_logs = [
            ("dev1", 8, 60),
            ("dev2", 9, 60),
        ]

        with patch(
            "app.feedback_engine.LogRepository.get_hourly_charging_counts_for_date",
            return_value=mock_logs,
        ):
            result = feedback_engine.calculate_daily_individual_feedback(
                mock_db_session, target_date
            )

        device_ids = {d["device_id"] for d in result["devices"]}
        assert len(result["devices"]) == 2
        assert device_ids == {"dev1", "dev2"}