import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# -----------------------------------------------------------------------------
# MySQL Connection Management Core
# -----------------------------------------------------------------------------
def get_db_engine():
    """Initializes a pooling SQLAlchemy connection engine for MySQL."""
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    database = os.getenv("DB_NAME", "battery_server_db")
    
    # Using pymysql dialect driver setup
    engine_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    return create_engine(engine_url, pool_recycle=3600)

def run_sql(query, params=None):
    """Executes a SELECT query and channels it straight to a Pandas DataFrame."""
    engine = get_db_engine()
    try:
        # Note: Pandas read_sql accepts dictionary parameters or sequences matching %s
        df = pd.read_sql_query(query, engine, params=params)
        return df
    except Exception as e:
        st.error(f"MySQL Data Retrieval Error: {e}")
        return pd.DataFrame()

def execute_sql(query, params=None):
    """Executes data mutation commands (UPDATE, INSERT, DELETE) safely."""
    engine = get_db_engine()
    if params is None:
        params = ()
    try:
        with engine.begin() as conn:
            # Wrap raw string query into an executable block
            conn.execute(text(query), params)
    except Exception as e:
        st.error(f"MySQL Execution Mutation Error: {e}")

# -----------------------------------------------------------------------------
# Data Access Objects (DAOs) adapted to MySQL
# -----------------------------------------------------------------------------
def get_tracker_settings():
    df = run_sql("SELECT * FROM tracker_settings LIMIT 1")
    if df.empty:
        st.error("tracker_settings table missing or uninitialized.")
        return {"interval_minutes": 20, "updated_at": datetime.now()}
    return df.iloc[0].to_dict()

def save_tracker_settings(interval_minutes):
    # MySQL uses :param syntax via text() wrapper or %s positions
    query = "UPDATE tracker_settings SET interval_minutes = :interval, updated_at = NOW() WHERE id = 1"
    execute_sql(query, {"interval": interval_minutes})

def get_network_settings():
    df = run_sql("SELECT * FROM network_settings LIMIT 1")
    if df.empty:
        st.error("network_settings table missing or uninitialized.")
        return {"server_url": "", "api_key": ""}
    return df.iloc[0].to_dict()

def save_network_settings(server_url, api_key):
    query = "UPDATE network_settings SET server_url = :url, api_key = :key, updated_at = NOW() WHERE id = 1"
    execute_sql(query, {"url": server_url, "key": api_key})

def get_tracker_status():
    df = run_sql("SELECT * FROM tracker_status LIMIT 1")
    if df.empty:
        return {"is_running": 0}
    return df.iloc[0].to_dict()

def save_tracker_status(is_running):
    query = "UPDATE tracker_status SET is_running = :status, updated_at = NOW() WHERE id = 1"
    execute_sql(query, {"status": is_running})

def get_all_devices():
    df = run_sql("SELECT DISTINCT device_name FROM battery_events WHERE device_name IS NOT NULL ORDER BY device_name")
    if df.empty:
        return []
    return df["device_name"].tolist()

# -----------------------------------------------------------------------------
# Dashboard App Pages
# -----------------------------------------------------------------------------
def page_event_explorer():
    st.header("🔍 Event Explorer")

    devices = ["All"] + get_all_devices()
    selected_device = st.selectbox("Device Name Select", devices)

    event_filter = st.selectbox(
        "Event Category Filter",
        ["All", "Only Specific Actions", "System Boundaries ('start', 'stop')"],
    )

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
    with col2:
        end_date = st.date_input("End Date", datetime.now())

    # Build MySQL Query Layout dynamically
    # Use standard relational syntax string variables
    query = "SELECT * FROM battery_events WHERE 1=1"
    params = {}

    if selected_device != "All":
        query += " AND device_name = :device_name"
        params["device_name"] = selected_device

    if event_filter == "Only Specific Actions":
        query += " AND event_type IS NOT NULL"
    elif event_filter == "System Boundaries ('start', 'stop')":
        query += " AND event_type IN ('start', 'stop')"

    query += " AND timestamp BETWEEN :start_ts AND :end_ts ORDER BY timestamp DESC"
    params["start_ts"] = f"{start_date} 00:00:00"
    params["end_ts"] = f"{end_date} 23:59:59"

    if st.button("Run Explorer Query", type="primary"):
        df = run_sql(query, params)
        st.metric("Records Found", len(df))
        st.dataframe(df, use_container_width=True)

def page_device_comparison():
    st.header("📊 Device Comparison Analytics")

    devices = get_all_devices()
    if not devices:
        st.info("No reported devices discovered in metrics database.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        dev_a = st.selectbox("Primary Node Device A", devices, key="dev_a")
    with col2:
        dev_b = st.selectbox("Comparison Node Device B", devices, key="dev_b")

    if st.button("Compute Processing Metrics"):
        # Metric Block 1: Basic Averages
        avg_df = run_sql("""
            SELECT device_name, AVG(battery_level) as avg_level 
            FROM battery_events 
            WHERE device_name IN %(devs)s GROUP BY device_name
        """, params={"devs": [dev_a, dev_b]})
        
        st.subheader("Mean Battery Levels")
        st.dataframe(avg_df, use_container_width=True)

        # Metric Block 2: MySQL Date Logic-based Daily Discharge Delta
        discharge_df = run_sql("""
            SELECT device_name, DATE(timestamp) AS day,
                   (MAX(battery_level) - MIN(battery_level)) AS discharge_delta
            FROM battery_events
            WHERE device_name IN %(devs)s
            GROUP BY device_name, DATE(timestamp)
            ORDER BY day DESC
        """, params={"devs": [dev_a, dev_b]})
        
        st.subheader("Daily Discharge Rates")
        st.dataframe(discharge_df, use_container_width=True)

def page_network_settings():
    st.header("🌐 Network Interface Configuration")
    net = get_network_settings()

    url = st.text_input("Server Base Target URL", value=net["server_url"])
    key = st.text_input("API Authorization Master Key", value=net["api_key"], type="password")

    if st.button("Apply Network Configuration"):
        save_network_settings(url, key)
        st.success("Database routing keys altered successfully.")

def page_tracker_settings():
    st.header("⏱️ Core Tracker Intervals")
    settings = get_tracker_settings()

    interval = st.slider("Logging Telemetry Frequency (Minutes)", 1, 60, int(settings["interval_minutes"]))

    if st.button("Update System Frequency"):
        save_tracker_settings(interval)
        st.success(f"System sync window modulated to {interval} minutes.")

def page_tracker_control():
    st.header("⚡ Live Mesh Orchestrator Controller")
    status = get_tracker_status()
    
    is_running = status.get("is_running", 0)
    st.write("Current Cluster Engine Status Flag:", "🟢 ACTIVE" if is_running else "🔴 PAUSED")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Signal Halt (Pause Logging Loop)", use_container_width=True):
            save_tracker_status(0)
            st.rerun()
    with col2:
        if st.button("Signal Resume (Activate Loop)", use_container_width=True, type="primary"):
            save_tracker_status(1)
            st.rerun()

# -----------------------------------------------------------------------------
# Application Router Base
# -----------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Central Battery Server Core Dashboard", layout="wide")
    st.sidebar.title("🔋 Server Control Deck")
    
    page = st.sidebar.radio(
        "Navigation Matrix",
        ["Event Explorer", "Device Comparison", "Network Profiles", "Tracker Intervals", "Global Loop Killswitch"]
    )

    if page == "Event Explorer":
        page_event_explorer()
    elif page == "Device Comparison":
        page_device_comparison()
    elif page == "Network Profiles":
        page_network_settings()
    elif page == "Tracker Intervals":
        page_tracker_settings()
    elif page == "Global Loop Killswitch":
        page_tracker_control()

if __name__ == "__main__":
    main()