import pandas as pd
import argparse
import logging
import os

from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from solar_processing.pi_dispatcher import PlantformMQTTDispatcher
from solar_processing.storage import SolarStorageManager

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)


def run_test(target: str, broker_ip: str):
    dispatcher = PlantformMQTTDispatcher(broker_ip=broker_ip, topic="prototypes")

    print(f"Sending test payload for {target} to {broker_ip} on topic 'prototypes'...")

    if target == "plantform":   
        # sample data for test
        """ 
        times = pd.date_range('2026-07-21 00:00', periods=24, freq='h')
        percentages = [
            0, 0, 0, 0, 0, 0, 0, 0,
            51.4, 71.7, 88.2, 96.2, 98.4, 94.8, 85.4, 70.3, 51.0, 29.5,
            0, 0, 0, 0, 0 ,0
        ]
        df = pd.DataFrame({"power_percentage": percentages}, index=times)
        success = dispatcher.dispatch_schedule(df)
        """

        #fetching real data for demo

        db_user = os.environ.get("MYSQL_USER", "root")
        db_pass = os.environ.get("MYSQL_PASSWORD", "")
        db_host = os.environ.get("MYSQL_HOST", "localhost")
        db_name = os.environ.get("MYSQL_DATABASE", "battery_tracker")

        engine = create_engine(f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}/{db_name}")
        SessionLocal = sessionmaker(bind=engine)

        db = SessionLocal()
        try:
            target_date = date.today()
            print(f"Fetching database schedule for target date: {target_date}")
            success = dispatcher.dispatch_schedule_from_db(db, target_date)
        finally:
            db.close()

    elif target == "energyshape":
        gain_value = "5"
        success = dispatcher.dispatch_gain(gain_value)

    elif target == "activate":
        print("Starting activation protocol...")
        success = dispatcher.run_activation_protocol()

    elif target == "display":
        print("Starting display protocol ( Power-on -> Dispatch schedule -> Power-off)")
        times = pd.date_range('2026-07-21 00:00', periods=24, freq='h')
        percentages = [
            0, 0, 0, 0, 0, 0, 0, 0,
            51.4, 71.7, 88.2, 96.2, 98.4, 94.8, 85.4, 70.3, 51.0, 29.5,
            0, 0, 0, 0, 0, 0
        ]
        df = pd.DataFrame({"power_percentage": percentages}, index=times)
        success = dispatcher.run_display_protocol(df)


    else:
        print(f"Unknown target: {target}")
        return

    if success:
        print("Successfully dispatched retained payload to Plantform")
    else:
        print("Failed to dispatch payload")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dispatch MQTT test instructions")
    parser.add_argument(
        "--target",
        choices=["plantform", "energyshape", "activate", "display"],
        default="plantform",
        help="Specify which device cammand profile to test"
    )
    parser.add_argument(
        "--ip",
        default="100.95.20.33", #melina
        #default="127.0.0.1",
        help="MQTT broker IP address"
    )
    args = parser.parse_args()
    run_test(target=args.target, broker_ip=args.ip)