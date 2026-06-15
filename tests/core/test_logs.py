from datetime import datetime, timedelta
from app.db.repositories.devices import DeviceRepository
from app.db.repositories.logs import LogRepository
from app import models

def test_get_logs_for_device(client, db_session):
    device = DeviceRepository.get_or_create(db_session, "device-123")

    now = datetime.utcnow()
    logs = [
        models.BatteryLog(
            device_id = device.id,
            timestamp = now - timedelta(minutes=i),
            level = 50 + i,
            plugged = False,
            event_type = "test",
        )
        for i in range(3)
    ]
    db_session.add_all(logs)
    db_session.commit()

    response = client.get(f"/logs/{device.id}?limit=2")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2

    assert data[0]["timestamp"] > data[1]["timestamp"]

def test_get_logs_for_missing_device(client, db_session):
    response = client.get("/logs/9999")
    assert response.status_code == 404

def test_get_logs_in_range(client, db_session):
    device = DeviceRepository.get_or_create(db_session, "device-abc")

    now = datetime.utcnow()

    inside = [
        models.BatteryLog(
            device_id = device.id,
            timestamp = now - timedelta(minutes=i),
            level = 40,
            plugged = True,
            event_type = "inside",
        )
        for i in range(3)
    ]

    outside = models.BatteryLog(
        device_id = device.id,
        timestamp = now - timedelta(days=1),
        level = 10,
        plugged = False,
        event_type = "outside",
    )

    db_session.add_all(inside + [outside])
    db_session.commit()

    start = (now - timedelta(minutes = 5)).isoformat()
    end = now.isoformat()

    response = client.get(
        f"/logs/{device.id}/range?start={start}&end={end}"
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 3
    assert all(log["event_type"] == "inside" for log in data)

def test_logs_range_missing_device(client):
    now = datetime.utcnow().isoformat()
    response = client.get(f"/logs/9999/range?start={now}&end={now}")
    assert response.status_code == 404