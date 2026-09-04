from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_session
from app.db.repositories.logs import LogRepository
from app.db.repositories.devices import DeviceRepository
from app.schemas import LogOut

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/{device_id}", response_model=list[LogOut])
def get_logs(
    device_id: str,
    limit: int = Query(default=100, gt=0, le=1000),
    db: Session = Depends(get_session),
):
    device = DeviceRepository.get_by_id(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    return LogRepository.get_logs_for_device(db, device.device_id, limit)


@router.get("/{device_id}/range", response_model=list[LogOut])
def get_logs_range(
    device_id: str,
    start: datetime,
    end: datetime,
    db: Session = Depends(get_session),
):
    device = DeviceRepository.get_by_id(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    return LogRepository.get_logs_in_range(db, device.device_id, start, end)
