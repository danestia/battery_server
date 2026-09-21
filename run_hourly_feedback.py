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

def run_hourly_feedback():
    broker_ip = os.environ.get("MQTT_BROKER_IP", "100.95.20.33")
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