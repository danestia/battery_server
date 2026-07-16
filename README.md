# Battery Server 🔋☀️

An intelligent, data-driven solar forecasting and battery charging optimization system. `battery_server` ingests live solar predictions, executes physical irradiance calculations, structures actionable charging targets, and dynamically serves them to hardware clients to optimize local battery charging alignment.

---

## 🏗️ System Architecture

The project is structured into three primary decoupled layers:

1. **Solar Processing Ingestion Pipeline**: Queries live weather and solar forecast arrays from the **PVNode API**, runs plane-of-array (POA) mathematical models using **`pvlib`**, and packages charging targets.
2. **FastAPI Web Engine**: A high-performance REST API that acts as a translator, serving scaled target payloads (0.000 to 1.000) to the external **PLANTFORM** hardware prototype.
3. **Analytics & Dashboards**: A multi-page **Streamlit** user interface offering device monitoring and team carbon-alignment tracking powered by the system's **Feedback Engine**.

---

## 📋 Prerequisites & Environment

* **Python**: `3.12`
* **Database**: Local **MySQL** Server

---

## 🛠️ Setup & Installation

Follow these steps to set up the application environment from scratch:

### 1. Clone & Set Up Python Environment
Activate your virtual environment and install all dependencies:
```bash
# Activate virtual environment (e.g. Linux/macOS)
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt

2. Configure the Environment (.env)

Create a .env file in the root directory of the project and populate it with your local credentials and API keys:
Code snippet

DATABASE_URL=mysql+pymysql://tracker:admin@localhost/battery_tracker
PVNODE_API_KEY= "YOUR API KEY"

# Central MySQL Connection Details
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=tracker
DB_PASSWORD=admin
DB_NAME=battery_tracker

# Explicit Fallbacks for Solar Storage Module
MYSQL_HOST=127.0.0.1
MYSQL_USER=tracker
MYSQL_PASSWORD=admin
MYSQL_DATABASE=battery_tracker

3. Initialize the Database & Seed Tables

Before running the server, configure your local MySQL database, generate SQLAlchemy model tables, and seed tracker control records:
Bash

# A. Log in to MySQL and create the database schema
mysql -u tracker -p -e "CREATE DATABASE IF NOT EXISTS battery_tracker;"

# B. Run the SQLAlchemy table generation script to build core schema models
python create_tables.py

SQL

-- C. Execute the following SQL seeding queries to prepare tracker controller defaults:
USE battery_tracker;

-- Create tracker_settings table if missing & seed control defaults
CREATE TABLE IF NOT EXISTS tracker_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    interval_minutes INT NOT NULL DEFAULT 20,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
INSERT INTO tracker_settings (id, interval_minutes) 
VALUES (1, 20) 
ON DUPLICATE KEY UPDATE id=id;

-- Create network_settings table if missing & seed connection defaults
CREATE TABLE IF NOT EXISTS network_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    server_url VARCHAR(255) DEFAULT '',
    api_key VARCHAR(255) DEFAULT '',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
INSERT INTO network_settings (id, server_url, api_key) 
VALUES (1, '[http://127.0.0.1:8000](http://127.0.0.1:8000)', '') 
ON DUPLICATE KEY UPDATE id=id;

-- Create tracker_status table if missing & seed execution state
CREATE TABLE IF NOT EXISTS tracker_status (
    id INT PRIMARY KEY AUTO_INCREMENT,
    is_running TINYINT(1) NOT NULL DEFAULT 1,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
INSERT INTO tracker_status (id, is_running) 
VALUES (1, 1) 
ON DUPLICATE KEY UPDATE id=id;

🚀 Execution Guide

Always ensure your virtual environment (.venv) is activated before running the services.
1. Ingest Daily Solar Data (Cron / Manual Ingestion)

To run the solar forecast extraction, physics processing engine, and write tomorrow's instructions directly to the MySQL database:
Bash

python run_solar_ingest.py

2. Launch the FastAPI Server

Runs the web gateway delivering operational parameters to physical edge modules:
Bash

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

3. Launch the Streamlit Dashboards

Launches the frontend visualization to monitor device heartbeat logs and aggregate charging analytics:
Bash

streamlit run streamlit/Dashboard.py

🧪 Running Tests

To prevent registry collision and database lock errors, tests must be run module by module rather than through a blanket global sweep.

Use the following commands to execute your verification suites cleanly:
Core Engine & API Tests:
Bash

python -m pytest tests/core

Solar Physics & Ingestion Pipeline Tests:
Bash

python -m pytest tests/solar_tests

💡 Quick Tips for Maintaining Your Setup

    Automatic Raw Schema Verification: SolarStorageManager will automatically verify and initialize the pvnode_raw_forecasts and pi_hourly_instructions tables inside your configured MySQL schema on execution, ensuring a frictionless bootstrap.

    Database Scaling vs. API Scaling: Raw target calculations are securely preserved in your database as true percentages (0.0 - 100.0) for precise tracking in the FeedbackEngine. The FastAPI layer is solely responsible for scaling these to decimal ratios (0.000 - 1.000) on retrieval, insulating physical client hardware integrations from core architectural changes.