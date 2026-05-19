import streamlit as st
import pandas as pd

from db import get_db
from app.db.repositories.devices import DeviceRepository
from app.db.repositories.logs import LogRepository

st.title("Device Details")

db = next(get_db())

device_ids = [d.id for d in DeviceRepository.get_all(db)]
selected_id = st.selectbox("Select device", device_ids)

device = DeviceRepository.get_by_id(db, selected_id)
last_log = LogRepository.get_last_log_for_device(db, selected_id)

st.subheader(f"Device: {device.device_id}")

st.write(f"Hostname: {device.hostname}")
st.write(f"OS: {device.os}")
st.write(f"Last seen: {device.last_seen}")

if last_log:
    st.write(f"Last Level: {last_log.level}")
    st.write(f"Last Event: {last_log.eventType}")
else:
    st.warning("No logs for this device")

logs = LogRepository.get_last_log_for_device(db, selected_id)
df = pd.DataFrame([{
    "Timestamp": l.timestamp,
    "Level": l.level,
    "Plugged": l.plugged,
    "Event": l.event_type,
} for l in logs])

st.subheader("Log History")
st.dataframe(df)