from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db.repositories.devices import DeviceRepository
from app.db.repositories.logs import LogRepository

router = APIRouter(prefix="/stats", tags=["stats"])

ONLINE_THRESHOLD_MINUTES = 5

@router.get("/devices")
def stats_devices(db: Session = Depends(get_db)):
    devices = DeviceRepository.get_all(db)
    total = len(devices)

    now = datetime.utcnow()
    online = 0
    offline = 0
    never_seen = 0

    for d in devices:
        has_logs = LogRepository.has_logs(db, d.id)

        if not has_logs:
            never_seen += 1
            continue

        if d.last_seen and (now - d.last_seen) <= timedelta(minutes=ONLINE_THRESHOLD_MINUTES):
            online += 1
        else:
            offline += 1

    return {
        "total_devices": total,
        "online_devices": online,
        "offline_devices": offline,
        "never_seen_devices": never_seen,
    }

@router.get("/device/{device_id}")
def stats_single_device(device_id: str, db: Session = Depends(get_db)):

    device = DeviceRepository.get_by_device_id(db, device_id)
    if not device:
        raise HTTPException(404, "Device not found")
    
    last_log = LogRepository.get_last_log_for_device(db, device.id)

    now = datetime.utcnow()
    last_seen = device.last_seen
    delta_minutes = None

    if last_seen:
        delta_minutes = (now - last_seen).total_seconds() / 60

    return {
        "device_id": device.device_id,
        "last_seen": last_seen,
        "time_since_last_seen_minutes": delta_minutes,
        "last_level": last_log.level if last_log else None,
        "last_event_type": last_log.event_type if last_log else None,
    }
