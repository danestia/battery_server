from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.devices import DeviceRepository
from app.db.repositories.logs import LogRepository
from app.schemas import IngestRequest

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("/")
def ingest(payload: IngestRequest, db: Session = Depends(get_db)):
    device = DeviceRepository.get_or_create(db, payload.device_id)

    LogRepository.insert_log(
        db=db,
        device_id=device.device_id,
        timestamp=payload.timestamp,
        level=payload.level,
        plugged=payload.plugged,
        localisation=payload.localisation,
        event_type=payload.event_type,
        event_chargelevel=payload.event_chargelevel,
    )
    DeviceRepository.update_last_seen(db, device)
    
    return {"status": "ok"}