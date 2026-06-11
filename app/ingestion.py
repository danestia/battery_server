from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_session
from app.db.repositories.devices import DeviceRepository
from app.db.repositories.logs import LogRepository
from app import schemas

router = APIRouter()

def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()

@router.post("/ingest")
def ingest(log: schemas.BatteryLogIn, db: Session = Depends(get_db)):
    try:
        device = DeviceRepository.get_or_create(db, log.device_id)

        LogRepository.insert_log(db, str(device.device_id), log)
        
        DeviceRepository.update_last_seen(db, device)

        db.commit()
        return {"status": "ok"}
    
    except Exception as e:
        db.rollback()
        print(f"[CRITICAL FAILURE] Ingest dropped payload: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database transaction aborted: {str(e)}"
        )