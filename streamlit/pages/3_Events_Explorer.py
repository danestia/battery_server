import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent)) # points to root battery_server directory

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from app.models import BatteryLog
from db import get_db
from app.db.repositories.devices import DeviceRepository
from app.db.repositories.logs import LogRepository

st.header("🔍 Event Explorer")

db = next(get_db())

# --- Filters ---
all_devices = DeviceRepository.get_all(db)
device_options = ["All Devices"] + [d.device_id for d in all_devices]
selected_device = st.selectbox("Filter by Device", device_options)

event_filter = st.selectbox(
    "Event Category Filter",
    ["All", "Only Specific Actions", "System Boundaries ('start', 'stop')"],
)

plugged_filter = st.selectbox(
    "Plugged Status",
    ["All", "Plugged (1)", "Unplugged (0)"]
)

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
with col2:
    end_date = st.date_input("End Date", datetime.now())

start_ts = datetime.combine(start_date, datetime.min.time())
end_ts = datetime.combine(end_date, datetime.max.time())

# --- Query Building with SQLAlchemy ---
query = db.query(BatteryLog).filter(
    BatteryLog.timestamp >= start_ts,
    BatteryLog.timestamp <= end_ts
)

if selected_device != "All Devices":
    query = query.filter(BatteryLog.device_id == selected_device)

if event_filter == "Only Specific Actions":
    query = query.filter(BatteryLog.event_type.isnot(None))
elif event_filter == "System Boundaries ('start', 'stop')":
    query = query.filter(BatteryLog.event_type.in_(['start', 'stop']))

if plugged_filter == "Plugged (1)":
    query = query.filter(BatteryLog.plugged == 1)
elif plugged_filter == "Unplugged (0)":
    query = query.filter(BatteryLog.plugged == 0)

logs = query.order_by(BatteryLog.timestamp.desc()).limit(1000).all()

# --- Results Rendering ---
st.metric("Records Found", len(logs))

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
    st.info("No logs found matching the selected criteria.")