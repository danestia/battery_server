from pydantic import BaseModel, ConfigDict
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
    model_config = ConfigDict(from_attributes=True)
    id: int
    first_seen: datetime
    last_seen: datetime

class LogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    device_id: int
    timestamp: datetime
    level: int
    plugged: bool
    localisation: Optional[str] = None
    event_type: Optional[str] = None
    event_chargelevel: Optional[int] = None

class IngestRequest(BaseModel):
    device_id: str
    timestamp: datetime
    level: int
    plugged: bool
    localisation: str | None = None
    event_type: str | None = None
    event_chargelevel: int | None = None

