import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

st.title("Precision Analytics")
st.write("Calculate exact operational durations")

def get_db_engine():
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    database = os.getenv("DB_NAME", "battery_tracker")
    return create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}", pool_recycle=3600)

def run_sql(query, params=None):
    engine = get_db_engine()
    try:
        return pd.read_sql_query(query, engine, params=params)
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame()

devices_df = run_sql("SELECT DISTINCT device_id FROM battery_logs WHERE device_id IS NOT NULL ORDER BY device_id")
devices = devices_df["device_id"].to_list() if not devices_df.empty() else []

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
    query = """
        SELECT timestamp, plugged, level 
        FROM battery_logs 
        WHERE device_id = %(device_id)s 
          AND timestamp BETWEEN %(start_ts)s AND %(end_ts)s
    """

    params = {
        "device_id": selected_device,
        "start_ts": f"{start_date} 00:00:00",
        "end_ts": f"{end_date} 23:59:59"
    }

    df = run_sql(query, params)
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