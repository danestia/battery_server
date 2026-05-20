import streamlit as st
import pandas as pd

from db import get_db
from app.db.repositories.logs import LogRepository

st.title("Events Explorer")

db = next(get_db())
logs = LogRepository.get_all(db)

df = pd.DataFrame([{
    "Device ID": l.device_id,
    "Timestamp": l.timestamp,
    "Level": l.level,
    "Plugged": l.plugged,
    "Event": l.event_type,
} for l in logs])

st.dataframe(df)