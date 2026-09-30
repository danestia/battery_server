import sys
from pathlib import Path

# Add root folder (for 'app') and streamlit folder to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
STREAMLIT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
sys.path.append(str(STREAMLIT_DIR))

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

st.title("Manage Network Whitelist")
st.write("Add, view, or remove permitted network locations for telemetry collection.")

# Explicitly point to the 'battery_tracker' database
def get_db_engine():
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    database = os.getenv("DB_NAME", "battery_tracker")  # <-- Fixed database name
    return create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}", pool_recycle=3600)

engine = get_db_engine()

def get_current_whitelist():
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT server_url FROM network_settings WHERE id = 1")).fetchone()
            if res and res[0]:
                return [u.strip() for u in res[0].split(",") if u.strip()]
    except Exception as e:
        st.error(f"Error fetching whitelist: {e}")
    return []

# --- 1. View Current Whitelist & Removal Section ---
st.subheader("Current Whitelist Settings")
current_whitelist = get_current_whitelist()

if current_whitelist:
    st.write("Permitted networks currently active:")
    for net in current_whitelist:
        st.markdown(f"- `{net}`")
    
    st.markdown("---")
    st.subheader("Remove from Whitelist")
    network_to_remove = st.selectbox("Select a network to remove", options=current_whitelist)
    
    if st.button("Remove Selected Network"):
        if network_to_remove:
            current_whitelist.remove(network_to_remove)
            updated_urls = ",".join(current_whitelist)
            try:
                with engine.begin() as conn:
                    conn.execute(
                        text("UPDATE network_settings SET server_url = :urls, updated_at = NOW() WHERE id = 1"),
                        {"urls": updated_urls}
                    )
                st.success(f"Network '{network_to_remove}' successfully removed from the whitelist!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update whitelist in database: {e}")
else:
    st.info("The whitelist is currently empty. Add a network below.")

st.markdown("---")

# --- 2. Discovered Networks Section ---
try:
    nets_df = pd.read_sql(
        text("SELECT DISTINCT localisation FROM battery_logs WHERE localisation IS NOT NULL ORDER BY localisation"),
        engine
    )
    known_networks = nets_df["localisation"].tolist() if not nets_df.empty else []
except Exception as e:
    known_networks = []

st.subheader("Discovered Networks from Logs")
if known_networks:
    st.write(known_networks)
else:
    st.info("No network locations recorded in battery logs yet.")

st.markdown("---")

# --- 3. Add to Whitelist Section ---
st.subheader("Add Whitelist Settings")
new_network_input = st.text_input("Enter network to add to whitelist (e.g., estia.local)")

if st.button("Add to Whitelist"):
    network_name = new_network_input.strip()
    if network_name:
        try:
            with engine.begin() as conn:
                res = conn.execute(text("SELECT server_url FROM network_settings WHERE id = 1")).fetchone()
                current_urls = res[0] if res and res[0] else ""
                
                url_list = [u.strip() for u in current_urls.split(",") if u.strip()]
                if network_name not in url_list:
                    url_list.append(network_name)
                    updated_urls = ",".join(url_list)
                    conn.execute(
                        text("UPDATE network_settings SET server_url = :urls, updated_at = NOW() WHERE id = 1"),
                        {"urls": updated_urls}
                    )
                    st.success(f"Network '{network_name}' successfully added to the whitelist!")
                    st.rerun()
                else:
                    st.warning(f"Network '{network_name}' is already in the whitelist.")
        except Exception as e:
            st.error(f"Failed to update whitelist in database: {e}")
    else:
        st.error("Please enter a valid network identifier.")