from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.db.base import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), unique=True, index=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, server_default=func.now(), onupdate=func.now())
    logs = relationship("BatteryLog", back_populates="device")

class BatteryLog(Base):
    __tablename__ = "battery_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.device_id"), index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    level = Column(Integer, nullable=False)
    plugged = Column(Boolean, nullable=False)

    localisation = Column(String(255), nullable=True)
    event_type = Column(String(32), nullable=True)
    event_chargelevel = Column(Integer, nullable=True)
    device = relationship("Device", back_populates="logs")