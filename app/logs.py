from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.db.repositories.logs import LogRepository
from app.db.repositories.devices import DeviceRepository
from app.schemas import LogOut

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("/{device_id}", response_model=list[LogOut])
def get_logs(device_id: str, limit: int = 100, db: Session = Depends(get_db)):
    device = DeviceRepository.get_by_id(db, device_id)
    if not device:
        raise HTTPException(404, "Device not found")
    return LogRepository.get_logs_for_device(db, device.id, limit)

@router.get("/{device_id}/range", response_model=list[LogOut])
def get_logs_range(
    device_id: str,
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
):
    device = DeviceRepository.get_by_id(db, device_id)
    if not device:
        raise HTTPException(404, "Device not found")
    return LogRepository.get_logs_in_range(db, device_id, start, end)
