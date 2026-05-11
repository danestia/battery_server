from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BatteryLogIn(BaseModel):
    device_id: str
    timestamp: datetime
    level: int
    plugged: bool
    localisation: str
    event_type: Optional[str] = None
    event_chargelevel: Optional[int] = None
