from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from uuid import uuid4

import models
import schema
from database import sessionLocal
from routers.auth import get_current_user

from jose import JWTError, jwt
from security.jwt import SECRET_KEY, ALGORITHM

# ===== AI IMPORTS =====
from ai.activity_model import ActivityModel
from ai.health_risk import assess_health_risk

# load AI model once
activity_ai = ActivityModel()

router = APIRouter(prefix="/device", tags=["Device Management"])


# -------------------------
# DB Dependency
# -------------------------
def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# Create Device
# -------------------------
@router.post("/create", response_model=schema.DeviceRead, status_code=status.HTTP_201_CREATED)
def create_device(
    device: schema.DeviceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    token = uuid4().hex

    new_device = models.Device(
        user_id=current_user.id,
        device_name=device.device_name,
        mac_address=device.mac_address,
        device_token=token
    )

    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device


# -------------------------
# List Devices
# -------------------------
@router.get("/", response_model=List[schema.DeviceRead])
def list_devices(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return (
        db.query(models.Device)
        .filter(models.Device.user_id == current_user.id)
        .order_by(models.Device.created_at.desc())
        .all()
    )


# -------------------------
# Get Device By ID
# -------------------------
@router.get("/{device_id}", response_model=schema.DeviceRead)
def get_device_by_id(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    device = (
        db.query(models.Device)
        .filter(
            models.Device.id == device_id,
            models.Device.user_id == current_user.id
        )
        .first()
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


# -------------------------
# Delete Device
# -------------------------
@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    device = (
        db.query(models.Device)
        .filter(
            models.Device.id == device_id,
            models.Device.user_id == current_user.id
        )
        .first()
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(device)
    db.commit()
    return {"message": "Deleted successfully"}


# -------------------------
# Receive Device Data (ESP32 / Flutter)
# -------------------------
@router.post(
    "/data",
    response_model=schema.HeartRateScanRead,
    status_code=status.HTTP_201_CREATED
)
def device_send_data(
    payload: schema.DeviceDataCreate,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = authorization.replace("Bearer", "").strip()

    current_user = None
    acting_device = None

    # -------- Try device_token (ESP32) --------
    acting_device = db.query(models.Device).filter(
        models.Device.device_token == token
    ).first()

    if acting_device:
        current_user = db.query(models.User).filter(
            models.User.id == acting_device.user_id
        ).first()
    else:
        # -------- Try JWT (Flutter) --------
        try:
            payload_jwt = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload_jwt.get("id")
            current_user = db.query(models.User).filter(
                models.User.id == user_id
            ).first()
            if not current_user:
                raise JWTError()
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

    # -------- Validate device --------
    device = db.query(models.Device).filter(
        models.Device.id == payload.device_id
    ).first()

    if not device:
        raise HTTPException(status_code=400, detail="device_id does not exist")

    if acting_device and acting_device.id != device.id:
        raise HTTPException(status_code=403, detail="Device token mismatch")

    if not acting_device and device.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Device does not belong to user")

    # -------- Timestamp --------
    try:
        ts = (
            datetime.fromisoformat(payload.timestamp)
            if payload.timestamp
            else datetime.utcnow()
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format")

    # save heart
    new_scan = models.HeartRateScan(
        user_id=current_user.id,
        device_id=device.id,
        heart_rate=payload.heart_rate,
        spo2=payload.spo2,
        temperature_c=payload.temperature_c,
        status=payload.status,
        steps_delta=payload.steps_delta,
        jumps_delta=payload.jumps_delta,
        total_steps=payload.total_steps,
        timestamp=ts
    )

    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)

   #ai
    motion_features = models.AIMotionFeatures(
        scan_id=new_scan.id,
        acc_mag_mean=payload.acc_mag_mean,
        acc_mag_std=payload.acc_mag_std,
        acc_mag_max=payload.acc_mag_max
    )

    db.add(motion_features)
    db.commit()

    #ai predictions
    features = {
        "heart_rate": new_scan.heart_rate,
        "spo2": new_scan.spo2,
        "temperature_c": new_scan.temperature_c,
        "steps_delta": new_scan.steps_delta or 0,
        "jumps_delta": new_scan.jumps_delta or 0,
        "acc_mag_mean": payload.acc_mag_mean or 0,
        "acc_mag_std": payload.acc_mag_std or 0,
        "acc_mag_max": payload.acc_mag_max or 0,
    }

    # Activity Prediction
    activity_result = activity_ai.predict(features)

    # Health Risk Assessment
    risk_result = assess_health_risk(features)

    # create ai activity record
    if risk_result["risk_level"] in ["fatigue", "danger"]:
        new_alert = models.Alert(
            user_id=current_user.id,
            scan_id=new_scan.id,
            severity="critical" if risk_result["risk_level"] == "danger" else "high",
            message=risk_result["reason"],
            read_status=False
        )
        db.add(new_alert)
        db.commit()

    return new_scan
