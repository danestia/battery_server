import logging
import os
import subprocess
from datetime import date
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("startup_catchup")

def check_and_catch_up() -> None:
    db_user = os.getenv("MYSQL_USER", "root")
    db_pass = os.getenv("MYSQL_PASSWORD", "")
    db_host = os.getenv("MYSQL_HOST", "localhost")
    db_name = os.getenv("MYSQL_DATABASE", "battery_tracker")

    engine = create_engine(f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}/{db_name}")
    SessionLocal = sessionmaker(bind=engine)

    db = SessionLocal()
    try:
        today_str = date.today().strftime("%Y-%m-%d")

        query = text("SELECT COUNT(*) FROM pi_hourly_instructions WHERE target_date = :t_date")
        result = db.execute(query, {"t_date": today_str}).scalar()

        if result == 0:
            logger.warning(f"Missing solar schedule for {today_str}. Running catch up ingestion")

            subprocess.run([
                "/home/dan/Documents/code/github_project/battery_server/.venv/bin/python",
                "/home/dan/Documents/code/github_project/battery_server/run_solar_ingest.py"
            ], check=True)

            logger.info("Catch-up ingestion complete")
        else:
            logger.info(f"Solar schedule for {today_str} is already present")

    except Exception as e:
        logger.error(f"Startup catch-up encountered a critical error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_and_catch_up()