from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_session
from app.models import Device
from app.models import BatteryLog

client = TestClient(app)

def test_ingest_creates_device_and_log(client, db_session):
    payload ={
        "device_id": "test-device-123",
        "timestamp": "2026-05-19T12:00:00Z",
        "level": 87,
        "plugged": False,
        "localisation": "home",
        "event_type": "battery",
        "event_chargelevel": 87
    }

    response = client.post("/ingest/", json=payload)
    assert response.status_code == 200

    device = db_session.query(Device).filter_by(device_id="test-device-123").first()
    assert device is not None

    log = db_session.query(BatteryLog).filter_by(device_id=device.id).first()
    assert log is not None
    assert log.level == 87
    assert log.plugged is False