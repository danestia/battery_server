import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from db import get_db
from app.db.repositories.devices import DeviceRepository
from app.db.repositories.logs import LogRepository

ONLINE_THRESHOLD_MINUTES = 5

st.title("Devices Overview")

db = next(get_db())
devices = DeviceRepository.get_all(db)

rows = []
now = datetime.utcnow()

for d in devices:
    last_log = LogRepository.get_last_log_for_device(db, d.id)
    has_logs = last_log is not None

    if not has_logs:
        status = "never seen"
    else:
        if d.last_seen and (now - d.last_seen) <= timedelta(minutes=ONLINE_THRESHOLD_MINUTES):
            status = "online"
        else:
            status = "offline"
        
    rows.append({
        "Device ID": d.device_id,
        "Hostname": d.hostname,
        "OS": d.os,
        "Last Seen": d.last_seen,
        "Status": status,
        "Last Level": last_log.level if last_log else None,
    })

df = pd.DataFrame(rows)
st.dataframe(df)