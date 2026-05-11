from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from .base import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True)
    last_seen = Column(DateTime, server_default=func.now(), onupdate=func.now())

class BatteryLog(Base):
    __tablename__ = "battery_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), index=True)
    timestamp = Column(DateTime, nullable=False)
    level = Column(Integer, nullable=False)
    plugged = Column(Boolean, nullable=False)

    localisation = Column(String, nullable=True)
    event_type = Column(String, nullable=True)
    event_chargelevel = Column(Integer, nullable=True)