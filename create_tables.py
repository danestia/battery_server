import logging

from app.db.base import Base
from app.db.engine import get_engine
from sqlalchemy.exc import SQLAlchemyError

from app.models import Device, BatteryLog

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        engine = get_engine()
        safe_url = engine.url._replace(password="***") if engine.url.password else engine.url
        logger.info(f"Connecting to database at: {safe_url}")

        Base.metadata.create_all(bind=engine)

        table_names = list(Base.metadata.tables.keys())
        logger.info(f"Successfully verified/created tables: {table_names}")

    except SQLAlchemyError as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

if __name__ == "__main__":
    main()

