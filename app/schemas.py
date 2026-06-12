from pydantic import BaseModel, ConfigDict, Field, AliasChoices
from datetime import datetime
from typing import Optional

class BatteryLogIn(BaseModel):
    device_id: str
    timestamp: datetime
    level: float
    plugged: bool
    localisation: str
    event_type: Optional[str] = None
    event_chargelevel: Optional[float] = None
    log_uuid: Optional[str] = Field(None, validation_alias=AliasChoices("uuid", "log_uuid"))

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
    log_uuid: Optional[str] = None
    timestamp: datetime
    level: float
    plugged: bool
    localisation: Optional[str] = None
    event_type: Optional[str] = None
    event_chargelevel: Optional[float] = None

