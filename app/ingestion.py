import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.db.repositories.devices import DeviceRepository
from app.db.repositories.logs import LogRepository
from app import schemas

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ingest")
def ingest(log: schemas.BatteryLogIn, db: Session = Depends(get_session)):
    try:
        device = DeviceRepository.get_or_create(db, log.device_id)

        LogRepository.insert_log(db, device.device_id, log)
        
        DeviceRepository.update_last_seen(db, device)

        db.commit()
        return {"status": "ok"}
    
    except Exception as e:
        db.rollback()
        logger.exception("Ingest endpoint failed to process log payload for device_id=%s", log.device_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database transaction failed while ingesting battery telemetry."        
        )