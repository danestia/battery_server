from datetime import datetime
from sqlalchemy import text

def test_ingest_endpoint(client, db_session):
    payload = {
        "device_id": "abc123",
        "timestamp": datetime.utcnow().isoformat(),
        "level": 90,
        "plugged": True,
        "event": "ingest_test"
    }

    response = client.post("/ingest", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    device = db_session.execute(text("SELECT * FROM devices")).fetchone()
    assert device is not None
    
    log = db_session.execute(text("SELECT * FROM devices")).fetchone()
    assert log is not None
    assert log.level == 90