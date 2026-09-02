import time
import uuid
from app import models
from app.db.repositories.devices import DeviceRepository
from app.db.repositories.logs import LogRepository
from app.schemas import BatteryLogIn
from datetime import datetime, timezone


def test_get_or_create_device(db_session):
    d1 = DeviceRepository.get_or_create(db_session, "repo_device_1")
    d2 = DeviceRepository.get_or_create(db_session, "repo_device_1")
    assert d1.id == d2.id
    assert d1.device_id == "repo_device_1"

def test_update_last_seen(db_session):
    device = DeviceRepository.get_or_create(db_session, "repo_device_2")
    DeviceRepository.update_last_seen(db_session, device)
    old_ts = device.last_seen

    time.sleep(1)

    DeviceRepository.update_last_seen(db_session, device)
    assert device.last_seen > old_ts

def test_insert_log(db_session):
    device = DeviceRepository.get_or_create(db_session, "repo_device_3")

    unique_uuid = f"test_uuid_{uuid.uuid4()}"

    log = BatteryLogIn(
        log_uuid=unique_uuid,
        device_id="repo_device_3",
        timestamp=datetime.utcnow(),
        level=42,
        plugged=True,
        localisation="office",
        event_type=None,
        event_chargelevel=None
    )
    LogRepository.insert_log(db_session, device.device_id, log)
    logs = db_session.query(models.BatteryLog).filter_by(device_id=device.device_id).all()
    assert len(logs) == 1
    assert logs[0].level == 42