import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

st.title("Manage Network Whitelist")
st.write("Add, view, or remove permitted network locations for telemetry collection.")

def get_db_engine():
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    database = os.getenv("DB_NAME", "battery_server_db")
    return create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}", pool_recycle=3600)

def run_sql(query, params=None):
    engine = get_db_engine()
    try:
        return pd.read_sql_query(query, engine, params=params)
    except Exception as e:
        return pd.DataFrame()

nets_df = run_sql("SELECT DISTINCT localisation FROM battery_logs WHERE localisation IS NOT NULL ORDER BY localisation")
known_networks = nets_df["localisation"].tolist() if not nets_df.empty else []

st.subheader("Discovered Networks from Logs")
if known_networks:
    st.write(known_networks)
else:
    st.info("No network locations recorded in battery logs yet")

st.subheader("Update Whitelist Settings")
new_network_input = st.text_input("Enter network to add to whitelist (eg estia.local)")

if st.button("Add to Whitelist"):
    network_name = new_network_input.strip()
    if network_name:
        engine = get_db_engine()
        try:
            with engine.begin() as conn:
                # Assuming you want to update a column or insert into a whitelist table.
                # For a comma-separated list in network_settings:
                res = conn.execute(text("SELECT server_url FROM network_settings WHERE id = 1")).fetchone()
                current_urls = res[0] if res and res[0] else ""
                
                # Append if not already in the list
                url_list = [u.strip() for u in current_urls.split(",") if u.strip()]
                if network_name not in url_list:
                    url_list.append(network_name)
                    updated_urls = ",".join(url_list)
                    conn.execute(
                        text("UPDATE network_settings SET server_url = :urls, updated_at = NOW() WHERE id = 1"),
                        {"urls": updated_urls}
                    )
                    st.success(f"Network '{network_name}' successfully added to the whitelist!")
                else:
                    st.warning(f"Network '{network_name}' is already in the whitelist.")
        except Exception as e:
            st.error(f"Failed to update whitelist in database: {e}")
    else:
        st.error("Please enter a valid network identifier.")