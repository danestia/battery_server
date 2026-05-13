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

class DeviceBase(BaseModel):
    device_id: str
    hostname: str | None = None
    os: str | None = None

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    hostname: str | None = None
    os: str | None = None

class DeviceOut(DeviceBase):
    id: int
    first_seen: datetime
    last_seen: datetime

    class Config:
        orm_mode = True