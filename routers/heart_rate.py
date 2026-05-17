from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import schema
import models
from database import sessionLocal
from routers.auth import get_current_user
from datetime import datetime
import logging
logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/heart", tags=["Heart Rate Scans"])


def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


def _maybe_create_alert(db: Session, user_id: int, scan: models.HeartRateScan, scan_id: Optional[int] = None):
    try:
        hr = scan.heart_rate
        sp = scan.spo2
        temp = scan.temperature_c
    except Exception as e:
        logger.exception("Failed to read scan values: %s", e)
        return None

    issues = []  # 👈 جديد: جمع الـ issues
    severity = "normal"

    # HR logic (updated thresholds)
    if hr is not None:
        if hr >= 140:  # Critical high (tachycardia severe)
            issues.append(f"Critical high heart rate: {hr} bpm")
            severity = "critical"
        elif hr >= 120:  # High
            issues.append(f"High heart rate: {hr} bpm")
            if severity != "critical":
                severity = "high"
        elif hr < 40:  # 👈 غيّر: <40 critical (كان <=40 low)
            issues.append(f"Critical low heart rate: {hr} bpm")
            severity = "critical"
        elif hr < 50:  # Low (50-40)
            issues.append(f"Low heart rate: {hr} bpm")
            if severity == "normal":
                severity = "low"

    # SpO2 logic (updated)
    if sp is not None:
        if sp <= 88:  # 👈 غيّر: <=88 critical (كان <90)
            issues.append(f"Critical low SpO2: {sp}%")
            severity = "critical"
        elif sp <= 92:  # Low (<=92)
            issues.append(f"Low SpO2: {sp}%")
            if severity != "critical":
                severity = "high" if severity == "normal" else severity  # ترقية لو normal
        elif sp < 95:  # Mild low
            issues.append(f"Mild low SpO2: {sp}%")
            if severity == "normal":
                severity = "low"


    # Temperature logic
    if temp is not None:
        if temp >= 39:
            issues.append(f"Critical high temperature: {temp} C")
            severity = "critical"
        elif temp >= 37.5:
            issues.append(f"High temperature: {temp} C")
            if severity != "critical":
                severity = "high"
        elif temp < 35:
            issues.append(f"Low temperature: {temp} C")
            if severity == "normal":
                severity = "low"

    if issues:  # 👈 جديد: لو فيه issues
        message = "; ".join(issues)  # جمع الرسائل
        try:
            new_alert = models.Alert(
                user_id=user_id,
                scan_id=scan_id,
                message=message,
                severity=severity,
                read_status=False
            )
            db.add(new_alert)
            db.commit()
            db.refresh(new_alert)
            logger.info("Alert created: id=%s user=%s scan=%s severity=%s message=%s", 
                        new_alert.id, user_id, scan_id, severity, message)
            return new_alert
        except Exception as e:
            db.rollback()
            logger.exception("Failed to create alert in DB: %s", e)
            return None
    return None


@router.post("/", response_model=schema.HeartRateScanRead, status_code=status.HTTP_201_CREATED)
def create_scan(
    scan: schema.HeartRateScanCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user_id = current_user.id
    device_id: Optional[int] = scan.device_id if scan.device_id else None

    if device_id is not None:
        device = db.query(models.Device).filter(models.Device.id == device_id).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="device_id does not exist")
        if device.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device does not belong to current user")

    new_scan = models.HeartRateScan(
        user_id=user_id,
        device_id=device_id,
        heart_rate=scan.heart_rate,
        spo2=scan.spo2,
        temperature_c=scan.temperature_c,
        status=scan.status,
        scan_type=scan.scan_type
    )

    try:
        db.add(new_scan)
        db.commit()
        db.refresh(new_scan)
    except Exception as e:
        db.rollback()
        logger.exception("Failed to create scan: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create scan")

    
    _maybe_create_alert(db, user_id, new_scan, scan_id=new_scan.id)

    return new_scan


from typing import List, Optional
from fastapi import Query

@router.get("/", response_model=List[schema.HeartRateScanRead])
def get_all_scans(
    start_date: Optional[str] = Query(None, description="ISO start datetime or YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="ISO end datetime or YYYY-MM-DD"),
    device_id: Optional[int] = Query(None),
    status: Optional[models.StatusEnum] = Query(None),
    min_hr: Optional[int] = Query(None),
    max_hr: Optional[int] = Query(None),
    min_spo2: Optional[int] = Query(None),
    max_spo2: Optional[int] = Query(None),
    min_temp: Optional[float] = Query(None),
    max_temp: Optional[float] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    q = db.query(models.HeartRateScan).filter(models.HeartRateScan.user_id == current_user.id)

    
    from datetime import datetime
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except Exception:
            start_dt = datetime.fromisoformat(start_date + "T00:00:00")
        q = q.filter(models.HeartRateScan.timestamp >= start_dt)
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except Exception:
            end_dt = datetime.fromisoformat(end_date + "T23:59:59")
        q = q.filter(models.HeartRateScan.timestamp <= end_dt)

    if device_id is not None:
        q = q.filter(models.HeartRateScan.device_id == device_id)

    if status is not None:
        q = q.filter(models.HeartRateScan.status == status)

    if min_hr is not None:
        q = q.filter(models.HeartRateScan.heart_rate >= min_hr)
    if max_hr is not None:
        q = q.filter(models.HeartRateScan.heart_rate <= max_hr)

    if min_spo2 is not None:
        q = q.filter(models.HeartRateScan.spo2 >= min_spo2)
    if max_spo2 is not None:
        q = q.filter(models.HeartRateScan.spo2 <= max_spo2)

    if min_temp is not None:
        q = q.filter(models.HeartRateScan.temperature_c >= min_temp)
    if max_temp is not None:
        q = q.filter(models.HeartRateScan.temperature_c <= max_temp)

    
    scans = q.order_by(models.HeartRateScan.timestamp.desc()).offset(skip).limit(limit).all()
    return scans



@router.get("/{scan_id}", response_model=schema.HeartRateScanRead)
def get_scan_by_id(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    scan = (
        db.query(models.HeartRateScan)
        .filter(models.HeartRateScan.id == scan_id, models.HeartRateScan.user_id == current_user.id)
        .first()
    )
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    return scan


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    scan = (
        db.query(models.HeartRateScan)
        .filter(models.HeartRateScan.id == scan_id, models.HeartRateScan.user_id == current_user.id)
        .first()
    )
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    db.delete(scan)
    db.commit()
    return {"message": "Deleted successfully"}
