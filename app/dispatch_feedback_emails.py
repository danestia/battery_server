import sys
import logging
import argparse

from datetime import date, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    
from app.db.session import get_session
from app.feedback_engine import FeedbackEngine
from app.db.repositories.devices import DeviceRepository
from app.email_notifier import EmailNotifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_daily_email_dispatch(target_date: date = None) -> int:
    if target_date is None:
        target_date = date.today()

    db = get_session()
    try:
        engine = FeedbackEngine()
        notifier = EmailNotifier()

        feedback_payload = engine.calculate_daily_individual_feedback(db, target_date)

        email_map = DeviceRepository.get_device_email_map(db)

        sent_count = 0

        for device_entry in feedback_payload.get("devices", []):
            device_id = device_entry["device_id"]
            recipient = email_map.get(device_id)

            if not recipient:
                logger.warning(
                    f"Device '{device_id}' had activity during work hours, but has no email recorded. Skipping..."
                )
                continue

            if notifier.send_individual_feedback(recipient, device_entry, feedback_payload["date"]):
                logger.info(f"Successfully dispatched feedback email to {recipient} ({device_id})")
                sent_count += 1

        logger.info(f"Completed dispatch: {sent_count} feedback emails sent for {target_date}")
        return sent_count
    finally:
        db.close()

if __name__ == "__main__":
    run_daily_email_dispatch()