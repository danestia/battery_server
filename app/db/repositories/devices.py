from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app import models, schemas


class DeviceRepository:

    @staticmethod
    def get_or_create(db: Session, device_id: str):
        device = db.execute(
            select(models.Device).where(models.Device.device_id == device_id)
        ).scalar_one_or_none()

        if device:
            return device
        
        device = models.Device(device_id=device_id)
        db.add(device)
        db.flush()
        db.refresh(device)
        return device

    @staticmethod
    def get_device_email_map(db: Session) -> Dict[str, str]:
        devices = db.execute(
            select(models.Device).where(models.Device.email.isnot(None))
        ).scalars().all()
        return {device.device_id: device.email for device in devices if device.email}
    
    @staticmethod
    def update_last_seen(db: Session, device):
        device.last_seen = datetime.now(timezone.utc).replace(tzinfo=None)
        db.flush()

    @staticmethod
    def get_all(db: Session):
        return list(db.execute(select(models.Device)).scalars().all())
    
    @staticmethod
    def get_by_id(db: Session, id: int) -> Optional[models.Device]:
        return db.get(models.Device, id)
    
    @staticmethod
    def create(db: Session, data: schemas.DeviceCreate) -> models.Device:
        device = models.Device(
            device_id=data.device_id,
            hostname=data.hostname,
            os=data.os,
        )
        db.add(device)
        db.flush()
        db.refresh(device)
        return device
    
    @staticmethod
    def update(db: Session, device: models.Device, data: schemas.DeviceUpdate) -> models.Device:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(device, field, value)
        device.last_seen = datetime.utcnow()
        db.flush()
        db.refresh(device)
        return device
    
    @staticmethod
    def delete(db: Session, device: models.Device) -> None:
        db.delete(device)
        db.flush()

    