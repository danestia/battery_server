from sqlalchemy.orm import Session
from app import models
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