from app.db.base import Base
from app.db.engine import get_engine

from app.models import Device
from app.models import BatteryLog


def main():
    engine = get_engine()
    print("Creating tables on: ", engine.url)
    Base.metadata.create_all(bind=engine)
    print("Done")

if __name__ == "__main__":
    main()

