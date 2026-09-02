import os
import smtplib
import logging
from email.message import EmailMessage
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EmailNotifier:
    def __init__(self):
        self.smtp_host = os.environ.get("SMTP_HOST", "localhost")
        self.smtp_port = int(os.environ.get("SMTP_PORT", 1025))
        self.sender_email = os.environ.get("SENDER_EMAIL", "solar_study@project.local")

    def send_individual_feedback(self, recipient_email: str, feedback_entry: Dict[str, Any], date_str: str) -> bool:
        msg = EmailMessage()
        msg["Subject"] = f"Solar Alignment Report - {date_str}"
        msg["From"] = self.sender_email
        msg["To"] = recipient_email

        body = (
            f"Hello,\n\n"
            f"{feedback_entry['feedback_text']}\n\n"
            f"Daily Metrics Summary ({date_str}):\n"
            f"- Solar Alignment Score: {feedback_entry['alignment_score_pct']}%\n"
            f"- Green Energy Captured: {feedback_entry['solar_energy_wh']} Wh\n"
            f"- Other/Grid Energy Consumed: {feedback_entry['other_energy_wh']} Wh\n"
            f"- Total Energy Consumed: {feedback_entry['total_energy_wh']} Wh\n\n"
            f"Thank you for participating in the solar energy study."
        )
        msg.set_content(body)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.send_message(msg)
            logger.info(f"Successfully sent feedback email to {recipient_email}")
            return True
        except Exception as err:
            logger.error(f"Failed to send feedback email to {recipient_email}: {err}")
            return False