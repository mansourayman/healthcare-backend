
from datetime import datetime
from sqlalchemy import (
    Column, Float, Integer, String, DateTime, Date, ForeignKey, Enum, Boolean, Text
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declarative_base
import enum




Base = declarative_base()


class StatusEnum(str, enum.Enum):
    normal = "normal"
    high = "high"
    low = "low"
    critical = "critical"


class ScanTypeEnum(str, enum.Enum):
    periodic = "periodic"
    manual = "manual"
    other = "other"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)
    dob = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    devices = relationship("Device", back_populates="user", cascade="all,delete-orphan")
    scans = relationship("HeartRateScan", back_populates="user", cascade="all,delete-orphan")
    activities = relationship("UserActivity", back_populates="user", cascade="all,delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all,delete-orphan")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_name = Column(String(50), nullable=True)
    mac_address = Column(String(50), nullable=True)
    device_token = Column(String(255), unique=True, nullable=True)  # NEW: device token
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="devices")
    scans = relationship("HeartRateScan", back_populates="device")



class HeartRateScan(Base):
    __tablename__ = "heart_rate_scans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    heart_rate = Column(Integer, nullable=True)
    spo2 = Column(Integer, nullable=True)
    temperature_c = Column(Float, nullable=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.normal)
    scan_type = Column(Enum(ScanTypeEnum), default=ScanTypeEnum.manual)
    steps_delta = Column(Integer, nullable=True)
    jumps_delta = Column(Integer, nullable=True)
    total_steps = Column(Integer, nullable=True)

    user = relationship("User", back_populates="scans")
    device = relationship("Device", back_populates="scans")
    
class AIMotionFeatures(Base):
    __tablename__ = "ai_motion_features"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("heart_rate_scans.id", ondelete="CASCADE"))
    acc_mag_mean = Column(Float)
    acc_mag_std = Column(Float)
    acc_mag_max = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)



class UserActivity(Base):
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    sleep_start = Column(DateTime, nullable=True)
    sleep_end = Column(DateTime, nullable=True)
    activity_level = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="activities")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scan_id = Column(Integer, ForeignKey("heart_rate_scans.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="low")
    read_status = Column(Boolean, default=False)

    user = relationship("User", back_populates="alerts")
    
    
