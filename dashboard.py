import streamlit as st
from sqlalchemy.orm import sessionmaker
from app.db.engine import get_engine
from app.db.repositories.devices import DeviceRepository
from app.db.repositories.logs import LogRepository
from app import models
from datetime import datetime, timedelta


st.set_page_config(
    page_title="Battery Tracker Server Dashboard",
    layout="wide",
)

def get_db():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def page_overview():
    st.header("Overview")
    db = get_db()
    try:
        devices = DeviceRepository.get_all(db)
        total = len(devices)
        now = datetime.utcnow()
        online, offline, never_seen = 0, 0, 0
        for d in devices:
            if not LogRepository.has_logs(db, d.id):
                never_seen += 1
            elif d.last_seen and (now - d.last_seen) <= timedelta(minutes=5):
                online += 1
            else:
                offline += 1

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Devices", total)
        col2.metric("Online", online)
        col3.metric("Offline", offline)
        col4.metric("Never Seen", never_seen)

        st.subheader("All Devices")
        if devices:
            data = [
                {
                    "ID": d.id,
                    "Device ID": d.device_id,
                    "First Seen": d.first_seen,
                    "Last Seen": d.last_seen,
                }
                for d in devices
            ]
            st.dataframe(data, use_container_width=True)
        else:
            st.info("No devices registered yet")
    finally:
        db.close()

def page_device_detail():
    st.header("Device Detail")
    db = get_db()
    try:
        devices = DeviceRepository.get_all(db)
        if not devices:
            st.info("No devices registered yet")
            return

        options = {f"{d.device_id} (id={d.id})": d.id for d in devices}
        selected = st.selectbox("Select device", list(options.keys()))
        device_id = options[selected]

        device = DeviceRepository.get_by_id(db, device_id)
        last_log = LogRepository.get_last_log_for_device(db, device_id)
        now = datetime.utcnow()

        col1, col2, col3 = st.columns(3)
        col1.metric("Last Level", f"{last_log.level}%" if last_log else "N/A")
        col2.metric("Plugged In", "Yes" if last_log and last_log.plugged else "No")
        col3.metric(
            "Last Seen",
            f"{round((now - device.last_seen).total_seconds() / 60)}m ago"
            if device.last_seen else "Never"
        )

        st.subheader("Recent Logs")
        limit = st.slider("Number of logs", 10, 200, 50)
        logs = LogRepository.get_logs_for_device(db, device_id, limit)
        if logs:
            data = [
                {
                    "Timestamp": l.timestamp,
                    "Level": l.level,
                    "Plugged": bool(l.plugged),
                    "Localisation": l.localisation,
                    "Event Type": l.event_type,
                    "Event Level": l.event_chargelevel,
                }
                for l in logs
            ]
            st.dataframe(data, use_container_width=True)
        else:
            st.info("No logs for this device")
    finally:
        db.close()

def page_log_explorer():
    st.header("Log Explorer")
    db = get_db()
    try:
        devices = DeviceRepository.get_all(db)
        if not devices:
            st.info("No devices registered yet")
            return
        
        options = {"All": None} | {f"{d.device_id} (id={d.id})" : d.id for d in devices}
        selected = st.selectbox("Device", list(options.keys()))
        device_id = options[selected]

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From", datetime.utcnow().date() - timedelta(days=7))
        with col2:
            end_date = st.date_input("To", datetime.utcnow().date())

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        if st.button("Run query..."):
            if device_id:
                logs = LogRepository.get_logs_in_range(db, device_id, start_dt, end_dt)
            else:
                logs = db.query(models.BatteryLog).filter(
                    models.BatteryLog.timestamp >= start_dt,
                    models.BatteryLog.timestamp <= end_dt,
                ).order_by(models.BatteryLog.timestamp.desc()).all()

            st.write(f"{len(logs)} rows")
            if logs:
                data = [
                    {
                        "Timestamp": l.timestamp,
                        "Device ID": l.device_id,
                        "Level": l.level,
                        "Plugged": bool(l.plugged),
                        "Localisation": l.localisation,
                        "Event Type": l.event_type,
                    }
                    for l in logs
                ]
                st.dataframe(data, use_container_width=True)
            else:
                st.info("No logs found")

    finally:
        db.close()

def page_tracker_settings():
    st.header("Tracker Settings")
    st.info("Controls for testing purposes")
    db = get_db()
    try:
        st.subheader("Registered Devices")
        devices = DeviceRepository.get_all(db)
        if devices:
            for d in devices:
                st.write(f"- '{d.device_id}' - last seen: {d.last_seen}")
        else:
            st.write("No devices registered")
    finally:
        db.close()

st.title("Battery Tracker Server Dashboard")

page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Device Detail", "Log Explorer", "Tracker Settings"]
)

if page == "Overview":
    page_overview()
elif page == "Device Detail":
    page_device_detail()
elif page == "Log Explorer":
    page_log_explorer()
elif page == "Tracker Settings":
    page_tracker_settings()