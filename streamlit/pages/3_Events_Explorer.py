import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from db import get_db
from app.db.repositories.logs import LogRepository
from app.db.repositories.devices import DeviceRepository

st.title("Events Explorer")

db = next(get_db())

all_devices = DeviceRepository.get_all(db)
device_options = ["All Devices"] + [d.device_id for d in all_devices]
selected_device = st.selectbox("Filter by Device", device_options)

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
with col2:
    end_date = st.date_input("End Date", datetime.now())

start_ts = datetime.combine(start_date, datetime.min.time())
end_ts = datetime.combine(end_date, datetime.max.time())

if selected_device != "All Devices":
    logs = LogRepository.get_logs_in_range(db, selected_device, start_ts, end_ts)
else:
    from app.models import BatteryLog
    logs = (
        db.query(BatteryLog)
        .filter(BatteryLog.timestamp >= start_ts)
        .filter(BatteryLog.timestamp <= end_ts)
        .order_by(BatteryLog.timestamp.desc())
        .limit(500)
        .all()
    )

if logs:
    parsed_logs = []
    for l in logs:
        log_obj = l[0] if isinstance(l, tuple) else l
        parsed_logs.append({
            "Timestamp": getattr(log_obj, "timestamp", None),
            "Device ID": getattr(log_obj, "device_id", "N/A"),
            "Level": f"{getattr(log_obj, 'level', 0.0)}%",
            "Plugged": getattr(log_obj, "plugged", False),
            "Event": getattr(log_obj, "event_type", "N/A"),
            "Location": getattr(log_obj, "localisation", "N/A"),
        })
    df = pd.DataFrame(parsed_logs)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No logs found matching the selected criteria")