import os
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import MagicMock

from app.feedback_engine import FeedbackEngine

SMTP_SERVER = "sandbox.smtp.mailtrap.io"
SMTP_PORT = 2525
MAILTRAP_USERNAME = "90946afcf80603"
MAILTRAP_PASSWORD = "806d7113efbc02"

SENDER_EMAIL = "dan.fleming@estia.fr"
RECIPIENT_EMAIL = "flemingdaniel@rocketmail.com"

def send_feedback_email(recipient: str, feedback_data: dict) -> None:
    report_lines = [
        f"Solar Alignment Feedback Report - {feedback_data['date']}",
        f"Max Possible Day Points: {feedback_data['max_possible_day_points']}",
        "-" * 40,
    ]

    for dev in feedback_data.get("devices", []):
        report_lines.append(
            f"Device ID: {dev['device_id']}\n"
            f"  Score: {dev['score_pct']}%\n"
            f"  Net Points: {dev['net_points_earned']}\n"
            f"  Plugged Hours: {dev['total_plugged_hours']}h\n"
            f"  Feedback: {dev['feedback_text']}\n"
        )

    body_text = "\n".join(report_lines)

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient
    msg["Subject"] = f"[Test] Battery Feedback Report - {feedback_data['date']}"
    msg.attach(MIMEText(body_text, "plain"))

    print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
        server.starttls()
        # Authenticate using Mailtrap credentials
        server.login(MAILTRAP_USERNAME, MAILTRAP_PASSWORD)
        server.send_message(msg)

    print(f"Email successfully delivered to Mailtrap Sandbox for {recipient}!")

if __name__ == "__main__":
    print("1. Initializing FeedbackEngine...")
    
    # Mock SolarStorageManager to isolate network/DB calls during email testing
    mock_solar = MagicMock()
    mock_solar.get_hourly_instructions_for_date.return_value = {}
    engine = FeedbackEngine(solar_storage=mock_solar)
    
    print("2. FeedbackEngine initialized.")

    sample_results = {
        "date": str(date.today()),
        "max_possible_day_points": 5.6,
        "devices": [
            {
                "device_id": "test_device_01",
                "score_pct": 85.0,
                "net_points_earned": 4.2,
                "total_plugged_hours": 6.0,
                "feedback_text": "Great job aligning charging with solar production!",
            }
        ],
    }

    send_feedback_email(RECIPIENT_EMAIL, sample_results)