from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True)
    first_seen = Column(DateTime, default=datetime.utcnow)

    logs = relationship("BatteryLog", back_populates="device")

class BatteryLog(Base):
    __tablename__ = "battery_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    timestamp = Column(DateTime, index=True)
    level = Column(Integer)
    plugged = Column(Boolean)
    event = Column(String)

    device = relationship("Device", back_populates="logs")
