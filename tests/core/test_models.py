from app import models
from datetime import datetime

def test_device_model(db_session):
    device = models.Device(device_id="model_test_device_1")
    db_session.add(device)
    db_session.commit()

    assert device.id is not None
    assert device.device_id == "model_test_device_1"

def test_batterylog_model(db_session):
    device = models.Device(device_id="model_test_device_2")
    db_session.add(device)
    db_session.commit()

    log = models.BatteryLog(
        device_id=device.device_id,
        timestamp=datetime.utcnow(),
        level=55,
        plugged=False,
        localisation="office",
        event_type=None,
        event_chargelevel=None,
    )
    db_session.add(log)
    db_session.commit()

    assert log.id is not None
    assert log.level == 55
    assert log.device_id == device.device_id

