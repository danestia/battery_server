import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent)) # points to root battery_server directory

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text

from db import get_db
from app.db.repositories.devices import DeviceRepository
from app.db.repositories.logs import LogRepository

st.title("Precision Analytics")
st.write("Calculate exact operational durations")

db = next(get_db())

all_devices = DeviceRepository.get_all(db)
devices = [d.device_id for d in all_devices] if all_devices else []

if not devices:
    st.warning("No devices found in the database")
    st.stop()

selected_device = st.selectbox("Select Device", devices)

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
with col2:
    end_date = st.date_input("End Date", datetime.now())

st.subheader("Time-Range Window Filter")
hour_col1, hour_col2 = st.columns(2)
with hour_col1:
    start_hour = st.slider("Start Hour (0-23)", 0, 23, 8)
with hour_col2:
    end_hour = st.slider("End Hour (0-23)", 0, 23, 18)

if st.button("Compute Precision Metrics", type="primary"):
    query = text("""
        SELECT timestamp, plugged, level 
        FROM battery_logs 
        WHERE device_id = :device_id 
          AND timestamp BETWEEN :start_ts AND :end_ts
    """)

    params = {
        "device_id": selected_device,
        "start_ts": f"{start_date} 00:00:00",
        "end_ts": f"{end_date} 23:59:59"
    }

    try:
        df = pd.read_sql(query, db.bind, params=params)
    except Exception as e:
        st.error(f"Database Error: {e}")
        df = pd.DataFrame()

    if df.empty:
        st.info("No logs matching selected criteria")
    else:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["hour"] = df["timestamp"].dt.hour

        window_df = df[(df["hour"] >= start_hour) & (df["hour"] <= end_hour)]

        plugged_count = window_df[window_df["plugged"] == 1].shape[0]
        unplugged_count = window_df[window_df["plugged"] == 0].shape[0]

        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Minutes Plugged In", f"{plugged_count} min")
        m_col2.metric("Minutes Unplugged", f"{unplugged_count} min")
        m_col3.metric("Total Heartbeats in Window", len(window_df))
        
        st.subheader("Filtered Log Sample")
        st.dataframe(window_df.head(100), use_container_width=True)