import streamlit as st
import pandas as pd

from db import get_db
from app.db.repositories.devices import DeviceRepository
from app.db.repositories.logs import LogRepository

st.title("Device Details")

db = next(get_db())

all_devices = DeviceRepository.get_all(db)

device_map = {d.device_id: d.id for d in all_devices}

if not device_map:
    st.info("No devices found in the database.")
    st.stop()

selected_device_name = st.selectbox("Select device", list(device_map.keys()))

selected_integer_id = device_map[selected_device_name]

device = DeviceRepository.get_by_id(db, selected_integer_id)

if not device:
    st.error("Device details could not be retrieved.")
    st.stop()

last_log = LogRepository.get_last_log_for_device(db, device.device_id)

st.subheader(f"Device: {device.device_id}")

st.write(f"**Device String ID:** {device.device_id}")
st.write(f"**Last seen:** {device.last_seen}")

if last_log:
    st.write(f"**Last Level:** {last_log.level}%")
    st.write(f"**Last Event:** {last_log.event_type}")
else:
    st.warning("No logs found for this device's status summary.")

st.subheader("Log History")

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