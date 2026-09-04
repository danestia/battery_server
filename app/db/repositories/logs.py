from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app import models

class LogRepository:

    @staticmethod
    def insert_log(db: Session, device_id: str, log):
        entry = models.BatteryLog(
            device_id=device_id,
            log_uuid=log.log_uuid,
            timestamp=log.timestamp,
            level=log.level,
            plugged=log.plugged,
            localisation=log.localisation,
            event_type=log.event_type,
            event_chargelevel=log.event_chargelevel
        )
        try:
            db.add(entry)
            db.commit()
            db.refresh(entry)
            return entry
        except IntegrityError:
            db.rollback()
            print(f"[INFO] Duplicate log caught: {log.log_uuid}. Skipping insertion")

            return (
                db.query(models.BatteryLog)
                .filter(models.BatteryLog.log_uuid ==log.log_uuid)
                .first()
            )

    @staticmethod
    def get_logs_for_device(db: Session, device_id: str, limit: int = 100):
        return (
            db.query(models.BatteryLog)
            .filter(models.BatteryLog.device_id == device_id)
            .order_by(models.BatteryLog.timestamp.desc())
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def get_logs_in_range(db: Session, device_id: str, start: datetime, end: datetime):
        return (
            db.query(models.BatteryLog)
            .filter(models.BatteryLog.device_id == device_id)
            .filter(models.BatteryLog.timestamp >= start)
            .filter(models.BatteryLog.timestamp <= end)
            .order_by(models.BatteryLog.timestamp.desc())
            .all()
        )
    
    @staticmethod
    def has_logs(db: Session, device_id: str) -> bool:
        return (
            db.query(models.BatteryLog)
            .filter(models.BatteryLog.device_id == device_id)
            .first()
            is not None
        )
    
    @staticmethod
    def get_last_log_for_device(db: Session, device_id: str):
        return (
            db.query(models.BatteryLog)
            .filter(models.BatteryLog.device_id == device_id)
            .order_by(models.BatteryLog.timestamp.desc())
            .first()
        )
    
    @staticmethod
    def get_hourly_charging_counts_for_date(db: Session, target_date: str) -> list:
        return (
            db.query(
                models.BatteryLog.device_id,
                func.hour(models.BatteryLog.timestamp).label("hour_index"),
                func.count(models.BatteryLog.id).label("heartbeat_count")
            )
            .filter(func.date(models.BatteryLog.timestamp) == target_date)
            .filter(models.BatteryLog.plugged == True)
            .group_by(models.BatteryLog.device_id, func.hour(models.BatteryLog.timestamp))
            .all()
        )