import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.db.repositories.devices import DeviceRepository
from app.db.repositories.logs import LogRepository
from app import schemas
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ingest")
def ingest(log: schemas.BatteryLogIn, db: Session = Depends(get_session)):
    try:
        # Server side whitelist validation
        settings_row = db.execute(text("SELECT server_url FROM network_settings WHERE id = 1")).fetchone()
        raw_whitelist = settings_row[0] if settings_row and settings_row[0] else ""
        allowed_networks = [net.strip() for net in raw_whitelist.split(",") if net.strip()]
        
        incoming_location = getattr(log, "localisation", None)

        # Enforce rule: If a whitelist is set, block any location not in it
        if allowed_networks and incoming_location not in allowed_networks:
            logger.warning("Rejected telemetry from unwhitelisted network: '%s' (Device: %s)", incoming_location, log.device_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Telemetry rejected: Origin network is not whitelisted."
            )

        device = DeviceRepository.get_or_create(db, log.device_id)

        LogRepository.insert_log(db, device.device_id, log)
        
        DeviceRepository.update_last_seen(db, device)

        db.commit()
        return {"status": "ok"}

    except HTTPException:
        raise
    
    except Exception as e:
        db.rollback()
        logger.exception("Ingest endpoint failed to process log payload for device_id=%s", log.device_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database transaction failed while ingesting battery telemetry."        
        )