from datetime import datetime

from sqlalchemy.orm import Session
from app import models

class LogRepository:

    @staticmethod
    def insert_log(
        db: Session,
        device_id: int,
        timestamp,
        level,
        plugged,
        localisation,
        event_type,
        event_chargelevel,
    ):
        entry = models.BatteryLog(
            device_id=device_id,
            timestamp=timestamp,
            level=level,
            plugged=plugged,
            localisation=localisation,
            event_type=event_type,
            event_chargelevel=event_chargelevel,
        )
        db.add(entry)
        db.commit()

    @staticmethod
    def get_logs_for_device(db: Session, device_id: int, limit: int = 100):
        return (
            db.query(models.BatteryLog)
            .filter(models.BatteryLog.device_id == device_id)
            .order_by(models.BatteryLog.timestamp.desc())
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def get_logs_in_range(db: Session, device_id: int, start: datetime, end: datetime):
        return (
            db.query(models.BatteryLog)
            .filter(models.BatteryLog.device_id == device_id)
            .filter(models.BatteryLog.timestamp >= start)
            .filter(models.BatteryLog.timestamp <= end)
            .order_by(models.BatteryLog.timestamp.desc())
            .all()
        )
    
    @staticmethod
    def has_logs(db, device_id: int) -> bool:
        return (
            db.query(models.BatteryLog)
            .filter(models.BatteryLog.device_id == device_id)
            .first()
            is not None
        )
    
    @staticmethod
    def get_last_log_for_device(db, device_id: int):
        return (
            db.query(models.BatteryLog)
            .filter(models.BatteryLog.device_id == device_id)
            .order_by(models.BatteryLog.timestamp.desc())
            .first()
        )