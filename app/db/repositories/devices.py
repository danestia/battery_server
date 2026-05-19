from sqlalchemy.orm import Session
from app import models
from app import schemas
from datetime import datetime

class DeviceRepository:

    @staticmethod
    def get_or_create(db: Session, device_id: str):
        device = db.query(models.Device).filter_by(device_id=device_id).first()
        if device:
            return device
        
        device = models.Device(device_id=device_id)
        db.add(device)
        db.commit()
        db.refresh(device)
        return device
    
    @staticmethod
    def update_last_seen(db: Session, device):
        device.last_seen = datetime.utcnow()
        db.commit()

    @staticmethod
    def list_all(db: Session):
        return db.query(models.Device).all()
    
    @staticmethod
    def get_by_id(db: Session, id_: int):
        return db.query(models.Device).filter(models.Device.id == id_).first()
    
    @staticmethod
    def create(db: Session, data: schemas.DeviceCreate):
        device = models.Device(
            device_id=data.device_id,
            hostname=data.hostname,
            os=data.os,
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        return device
    
    @staticmethod
    def update(db: Session, device, data: schemas.DeviceUpdate):
        for field, value in data.dict(exclude_unset=True).items():
            setattr(device, field, value)
        device.last_seen = datetime.utcnow()
        db.commit()
        db.refresh(device)
        return device
    
    @staticmethod
    def delete(db: Session, device):
        db.delete(device)
        db.commit()

    @staticmethod
    def get_all(db):
        return db.query(models.Device).all()
    
    @staticmethod
    def get_by_id(db, device_id: int):
        return db.query(models.Device).filter(models.Device.id == device_id).first()
        