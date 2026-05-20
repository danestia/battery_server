from datetime import datetime
from sqlalchemy import text

def test_ingest_endpoint(client, db_session):
    payload = {
        "device_id": "ingest_test_device",
        "timestamp": datetime.utcnow().isoformat(),
        "level": 90,
        "plugged": True,
        "localisation": "office",
        "event_type": "ingest_test",
        "event_chargelevel": None,
    }

    response = client.post("/ingest", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    device = db_session.execute(
        text("SELECT * FROM devices WHERE device_id = 'ingest_test_device'")
    ).fetchone()    
    assert device is not None
    
    log = db_session.execute(
        text("SELECT * FROM battery_logs WHERE device_id = :did ORDER BY timestamp DESC LIMIT 1"),
        {"did": device.id}
    ).fetchone()    
    assert log is not None
    assert log.level == 90