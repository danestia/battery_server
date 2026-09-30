import streamlit as st
from db import get_db
from app.db.repositories.devices import DeviceRepository
import sys
from pathlib import Path

# Add the parent directory (battery_server/) to Python's module search path
sys.path.append(str(Path(__file__).resolve().parent.parent))

st.set_page_config(
    page_title="Battery Server Dashboard",
    page_icon="🔋",
    layout="wide"
)

def main():
    # --- Landing Page Header ---
    st.title("🔋 Battery Server Dashboard")
    st.markdown(
        "Welcome to the central telemetry control deck. "
        "Use the sidebar navigation menu on the left to switch between modules:"
    )

    # Quick overview bullets or summary cards
    st.markdown("""
    - **Devices Overview & Details:** Monitor live node status, connectivity, and telemetry history.
    - **Event Explorer:** Filter and search through granular event logs and timestamps.
    - **Precision Analytics:** Calculate exact operational windows (plugged vs. unplugged durations).
    - **Manage Network Whitelist:** Configure permitted server locations and inspect discovered networks.
    """)

    st.markdown("---")

    # Quick metrics preview from the database
    try:
        db = next(get_db())
        total_devices = len(DeviceRepository.get_all(db))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Registered Devices", total_devices)
        with col2:
            st.metric("Cluster Status", "🟢 Online")
    except Exception:
        st.info("Database connection initializing or offline.")

if __name__ == "__main__":
    main()