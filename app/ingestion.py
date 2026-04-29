from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.db.repositories.devices import DeviceRepository
from app.db.repositories.logs import LogRepository
from app import schemas

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/ingest")
def ingest(log: schemas.BatteryLogIn, db: Session = Depends(get_db)):
    device = DeviceRepository.get_or_create(db, log.device_id)
    LogRepository.insert_log(db, device.id, log)
    DeviceRepository.update_last_sen(db, device)

    return {"status": "ok"}
