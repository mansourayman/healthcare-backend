
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime, date



class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    dob: Optional[date] = None
    gender: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)



class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"



class DeviceBase(BaseModel):
    device_name: Optional[str] = None
    mac_address: Optional[str] = None

class DeviceCreate(DeviceBase):
    
    pass

class DeviceRead(DeviceBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    device_token: Optional[str] = None   # new - token visible when returned

    model_config = ConfigDict(from_attributes=True)



# في schema.py
class HeartRateScanBase(BaseModel):
    heart_rate: int
    spo2: int
    temperature_c: Optional[float] = None
    status: Optional[str] = "normal"
    scan_type: Optional[str] = "manual"
    steps_delta: Optional[int] = None       # جديد
    jumps_delta: Optional[int] = None       # جديد
    total_steps: Optional[int] = None       # جديد

class HeartRateScanCreate(HeartRateScanBase):
    device_id: Optional[int] = None

class HeartRateScanRead(HeartRateScanBase):
    id: int
    user_id: int
    device_id: Optional[int] = None
    timestamp: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserActivityBase(BaseModel):
    date: date
    sleep_start: Optional[datetime] = None
    sleep_end: Optional[datetime] = None
    activity_level: Optional[int] = None
    notes: Optional[str] = None

class UserActivityCreate(UserActivityBase):
    
    pass

class UserActivityRead(UserActivityBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)



class AlertBase(BaseModel):
    message: str
    severity: Optional[str] = "low"
    read_status: Optional[bool] = False

class AlertCreate(AlertBase):
    
    scan_id: Optional[int] = None

class AlertRead(AlertBase):
    id: int
    user_id: int
    scan_id: Optional[int] = None
    timestamp: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
class DeviceDataCreate(BaseModel):
    device_id: int
    heart_rate: int
    spo2: int
    temperature_c: Optional[float] = None
    status: Optional[str] = "normal"
    timestamp: Optional[str] = None

    steps_delta: Optional[int] = None
    jumps_delta: Optional[int] = None
    total_steps: Optional[int] = None

    # AI FEATURES (NEW)
    acc_mag_mean: Optional[float] = None
    acc_mag_std: Optional[float] = None
    acc_mag_max: Optional[float] = None
