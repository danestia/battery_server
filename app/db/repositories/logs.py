from sqlalchemy.orm import Session
from app import models

class LogRepository:

    @staticmethod
    def insert_log(db: Session, device_id: int, log):
        entry = models.BatteryLog(
            device_id=device_id,
            timestamp=log.timestamp,
            level=log.level,
            plugged=log.plugged,
            localisation=log.localisation,
            event_type=log.event_type,
            event_chargelevel=log.event_chargelevel
        )
        db.add(entry)
        db.commit()