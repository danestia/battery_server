"""
Run Hourly Feedback Module
--------------------------
Production entry point executed hourly via cron to compute the current 
day's team performance score using FeedbackEngine and dispatch it 
to the energyshape MQTT endpoint.
"""

import os
import logging
from datetime import date
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from solar_processing.pi_dispatcher import PlantformMQTTDispatcher
from app.feedback_engine import FeedbackEngine

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

def run_hourly_feedback():
    broker_ip = os.environ.get("MQTT_BROKER_IP")
    if not broker_ip:
        raise ValueError(
            "MQTT_BROKER_IP environment variable is not set. " \
            "Please configure in .env"
        )
    topic = os.environ.get("MQTT_TOPIC", "prototypes")
    
    db_user = os.environ.get("MYSQL_USER", "root")
    db_pass = os.environ.get("MYSQL_PASSWORD", "")
    db_host = os.environ.get("MYSQL_HOST", "localhost")
    db_name = os.environ.get("MYSQL_DATABASE", "battery_tracker")

    engine = create_engine(f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}/{db_name}")
    SessionLocal = sessionmaker(bind=engine)

    db = SessionLocal()
    try:
        feedback_engine = FeedbackEngine()
        target_date = date.today()

        team_score_str = feedback_engine.calculate_daily_team_feedback(db, target_date)
        logging.info(f"Calculated team score for {target_date}: {team_score_str}")

        dispatcher = PlantformMQTTDispatcher(broker_ip=broker_ip, topic=topic)
        success = dispatcher.dispatch_gain(team_score_str)

        if success:
            logging.info(f"Successfully dispaatched team score {team_score_str} to energySHAPE")
        else:
            logging.error("Failed to dispatch team score")
    finally:
        db.close()

if __name__ == "__main__":
    run_hourly_feedback()