from app import models
from app.db.repositories.devices import DeviceRepository
from app.db.repositories.logs import LogRepository
from app.schemas import BatteryLogIn
from datetime import datetime

def test_get_or_create_device(db_session):
    d1 = DeviceRepository.get_or_create(db_session, "abc123")
    d2 = DeviceRepository.get_or_create(db_session, "abc123")

    assert d1.id == d2.id
    assert d1.device_id == "abc123"

def test_update_last_seen(db_session):
    device = DeviceRepository.get_or_create(db_session, "abc123")
    old_ts = device.last_seen

    DeviceRepository.update_last_seen(db_session, device)
    assert device.last_seen > old_ts

def test_insert_log(db_session):
    device = DeviceRepository.get_or_create(db_session, "abc123")

    log = BatteryLogIn(
        device_id="abc123",
        timestamp=datetime.utcnow(),
        level=42,
        plugged=True,
        event="repo_test"
    )

    LogRepository.insert_log(db_session, device.id, log)

    logs = db_session.query(models.BatteryLog).all()
    assert len(logs) == 1
    assert logs[0].level == 42
    
    