import os
import logging
from datetime import date
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from solar_processing.pi_dispatcher import PlantformMQTTDispatcher

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

def main():
    broker_ip = os.environ.get("MQTT_BROKER_IP", "100.95.20.33")
    topic = os.environ.get("MQTT_TOPIC", "prototypes")

    db_user = os.environ.get("MYSQL_USER", "root")
    db_pass = os.environ.get("MYSQL_PASSWORD", "")
    db_host = os.environ.get("MYSQL_HOST", "localhost")
    db_name = os.environ.get("MYSQL_DATABASE", "battery_tracker")

    engine = create_engine(f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}/{db_name}")
    SessionLocal = sessionmaker(bind=engine)

    dispatcher = PlantformMQTTDispatcher(broker_ip=broker_ip, topic=topic)
    db = SessionLocal()
    try:
        target_date = date.today()
        logging.info(f"Running morning dispatch for target date: {target_date}")

        success = dispatcher.dispatch_schedule_from_db(db, target_date)
        if success:
            logging.info("Morning schedule dispatch complete")
        else:
            logging.info("Morning schedule dispatch failed")
    finally:
        db.close()

if __name__ == "__main__":
    main()