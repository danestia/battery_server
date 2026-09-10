import os
from datetime import date
from typing import Dict, Any
from unittest.mock import MagicMock

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

from app.feedback_engine import FeedbackEngine
from app.db.repositories.logs import LogRepository

Base = declarative_base()


class SampleHeartbeatLog(Base):
    __tablename__ = "heartbeat_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    is_plugged_in = Column(Integer, nullable=False)


class FeedbackDemoRunner:

    def __init__(self) -> None:

        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        self.mock_solar_storage = MagicMock()
        self.feedback_engine = FeedbackEngine(solar_storage=self.mock_solar_storage)

    def seed_sample_data(self, target_date: date) -> None:
        sample_solar_data = {
            8: 20.0,
            9: 30.0,
            10: 60.0,
            11: 100.0,
            12: 100.0,
            13: 100.0,
            14: 90.0,
            15: 50.0,
            16: 20.0,
            17: 10.0,
        }
        self.mock_solar_storage.get_hourly_instructions_for_date.return_value = (
            sample_solar_data
        )

        sample_logs = []

        for h in range(11, 15):
            sample_logs.append(("eco_hero", h, 60))

        for h in range(16, 18):
            sample_logs.append(("night_owl", h, 60))

        for h in range(8, 18):
            sample_logs.append(("half_time", h, 30))

        return sample_logs


    def run(self, target_date: date) -> Dict[str, Any]:
        sample_logs = self.seed_sample_data(target_date)

        session = self.SessionLocal()
        try:
            LogRepository.get_hourly_charging_counts_for_date = (
                lambda db, date_str: sample_logs
            )

            results = self.feedback_engine.calculate_daily_individual_feedback(
                session, target_date
            )
            return results
        finally:
            session.close()


def print_formatted_results(results: Dict[str, Any]) -> None:

    print("=" * 60)
    print(f" SOLAR ALIGNMENT FEEDBACK REPORT FOR {results['date']}")
    print(f" Max Day Points Possible: {results['max_possible_day_points']}")
    print("=" * 60)

    for dev in results["devices"]:
        print(f"\n📱 Device: {dev['device_id']}")
        print(f"   ├─ Score:              {dev['score_pct']}%")
        print(f"   ├─ Net Earned Points:  {dev['net_points_earned']}")
        print(f"   ├─ Positive Points:    +{dev['positive_points']}")
        print(f"   ├─ Negative Points:    -{dev['negative_points']}")
        print(f"   ├─ Good / Bad Hours:   {dev['good_action_hours']}h good / {dev['bad_action_hours']}h bad")
        print(f"   ├─ Plugged Hours:      {dev['total_plugged_hours']}h total")
        print(f"   └─ Feedback: \"{dev['feedback_text']}\"")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo = FeedbackDemoRunner()
    results = demo.run(date(2026, 9, 10))
    print_formatted_results(results)