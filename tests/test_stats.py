from datetime import datetime, timedelta
from app.db.repositories.devices import DeviceRepository
from app import models

def test_stats_devices_overview(client, db_session):
    now = datetime.utcnow()

    device_a = DeviceRepository.get_or_create(db_session, "stats-dev-A")
    device_a.last_seen = now
    db_session.commit()

    device_b = DeviceRepository.get_or_create(db_session, "stats-dev-B")
    device_b.last_seen = now - timedelta(minutes=10)
    db_session.commit()

    device_c = DeviceRepository.get_or_create(db_session, "stats-dev-C")
    db_session.commit()

    log_a = models.BatteryLog(
        device_id = device_a.id,
        timestamp = now,
        level = 80,
        plugged = False,
        event_type = "test",
    )
    log_b = models.BatteryLog(
        device_id = device_b.id,
        timestamp = now - timedelta(minutes=20),
        level = 60,
        plugged = True,
        event_type = "test",
    )
    db_session.add_all([log_a, log_b])
    db_session.commit()

    response = client.get("/stats/devices")
    assert response.status_code == 200

    data = response.json()

    assert data["total_devices"] >= 3
    assert data["online_devices"] >= 1
    assert data["offline_devices"] >= 1
    assert data["never_seen_devices"] >= 1

def test_stats_single_device(client, db_session):
    now = datetime.utcnow()

    device = DeviceRepository.get_or_create(db_session, "dev-X")
    device.last_seen = now - timedelta(minutes=3)
    db_session.commit()

    log = models.BatteryLog(
        device_id = device.id,
        timestamp = now - timedelta(minutes=3),
        level = 42,
        plugged = False,
        event_type = "heartbeat",
    )
    db_session.add(log)
    db_session.commit()

    response = client.get(f"/stats/device/{device.device_id}")
    assert response.status_code == 200

    data = response.json()

    assert data["device_id"] == device.device_id
    assert data["last_seen"] is not None
    assert data["time_since_last_seen_minutes"] >= 3
    assert data["last_level"] == 42
    assert data["last_event_type"] == "heartbeat"

def test_stats_single_device_missing(client):
    response = client.get("/stats/device/99999")
    assert response.status_code == 404
