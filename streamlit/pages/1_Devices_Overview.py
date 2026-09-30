import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
STREAMLIT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
sys.path.append(str(STREAMLIT_DIR))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

st.title("Devices Overview")

ONLINE_THRESHOLD_MINUTES = 5

# Direct engine connection to battery_tracker
user = os.getenv("DB_USER", "root")
password = os.getenv("DB_PASSWORD", "")
host = os.getenv("DB_HOST", "127.0.0.1")
port = os.getenv("DB_PORT", "3306")
database = "battery_tracker"

engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}", pool_recycle=3600)

try:
    # Fetch devices and logs directly via SQL
    devices_df = pd.read_sql("SELECT * FROM devices", engine)
    logs_df = pd.read_sql("SELECT * FROM battery_logs ORDER BY timestamp DESC", engine)

    if devices_df.empty:
        st.warning("No devices found in the `devices` table.")
    else:
        rows = []
        now = datetime.utcnow()

        for _, d in devices_df.iterrows():
            dev_id = d.get("id")
            dev_str_id = d.get("device_id")

            # Match logs for this device using either primary key 'id' or string 'device_id'
            matched_logs = pd.DataFrame()
            if not logs_df.empty:
                if "device_id" in logs_df.columns:
                    matched_logs = logs_df[(logs_df["device_id"] == dev_id) | (logs_df["device_id"] == dev_str_id)]
                elif "device_fk" in logs_df.columns:
                    matched_logs = logs_df[logs_df["device_fk"] == dev_id]

            # Get the latest log for this device
            last_log = matched_logs.iloc[0] if not matched_logs.empty else None

            # Determine status
            last_seen = d.get("last_seen")
            if last_log is not None and "timestamp" in last_log:
                # Fallback to log timestamp if device last_seen is missing
                last_seen = last_seen or last_log["timestamp"]

            if last_log is None and pd.isna(last_seen):
                status = "no logs found for device"
            elif last_seen and (now - pd.to_datetime(last_seen)) <= timedelta(minutes=ONLINE_THRESHOLD_MINUTES):
                status = "online"
            else:
                status = "offline"

            rows.append({
                "Device ID": dev_str_id or dev_id,
                "Last Seen": last_seen,
                "Status": status,
                "Last Level": last_log["level"] if last_log is not None and "level" in last_log else None,
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)

        # Optional debug expander to inspect raw tables if needed
        with st.expander("🔍 Raw Data Inspector"):
            st.write("**Devices Table:**", devices_df)
            st.write("**Battery Logs Table (Latest 10):**", logs_df.head(10))

except Exception as e:
    st.error(f"Database query error: {e}")