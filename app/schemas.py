from pydantic import BaseModel
from datetime import datetime

class BatteryLogIn(BaseModel):
    device_id: str
    timestamp: datetime
    level: int
    plugged: bool
    event: str
