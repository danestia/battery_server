import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent)) # points to root battery_server directory

import streamlit as st
import pandas as pd
from db import get_db
from app.db.repositories.devices import DeviceRepository
from app.db.repositories.logs import LogRepository

st.header("📱 Device Details & Telemetry")

db = next(get_db())

all_devices = DeviceRepository.get_all(db)
device_map = {d.device_id: d.id for d in all_devices}

if not device_map:
    st.info("No reported devices discovered in metrics database.")
    st.stop()

selected_device_name = st.selectbox("Select Device Node", list(device_map.keys()))
selected_integer_id = device_map[selected_device_name]

device = DeviceRepository.get_by_id(db, selected_integer_id)

if not device:
    st.error("Device details could not be retrieved.")
    st.stop()

last_log = LogRepository.get_last_log_for_device(db, device.device_id)

# --- Metrics Layout ---
col1, col2 = st.columns(2)
with col1:
    st.metric("Device Identifier", device.device_id)
    if device.last_seen:
        st.write(f"**Last Seen:** {device.last_seen}")
with col2:
    if last_log:
        st.metric("Latest Level", f"{last_log.level}%")
        st.write(f"**Latest Event Type:** {last_log.event_type or 'None'}")
    else:
        st.warning("No logs found for this device's status summary.")

st.subheader("Historical Telemetry Log")

history_logs = LogRepository.get_logs_for_device(db, device.device_id)

if history_logs:
    parsed_logs = []
    for l in history_logs:
        log_obj = l[0] if isinstance(l, tuple) else l
        
        parsed_logs.append({
            "Timestamp": getattr(log_obj, "timestamp", None),
            "Level": getattr(log_obj, "level", 0.0),
            "Plugged": getattr(log_obj, "plugged", False),
            "Event": getattr(log_obj, "event_type", "N/A"),
            "Localisation": getattr(log_obj, "localisation", "Unknown")
        })
        
    df = pd.DataFrame(parsed_logs)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No historical logs recorded for this device.")