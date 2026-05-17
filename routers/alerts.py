from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schema
from ..database import sessionLocal
from .auth import get_current_user

router = APIRouter(prefix="/alerts", tags=["Health Alerts"])

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schema.AlertRead, status_code=status.HTTP_201_CREATED)
def create_alert(
    alert: schema.AlertCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    ينشئ تنبيه (Alert) للمستخدم الحالي.
    لا يعتمد على alert.user_id من الطلب — يستخدم current_user.id.
    """
    new_alert = models.Alert(
        user_id=current_user.id,
        scan_id=alert.scan_id,
        severity=alert.severity,
        message=alert.message,
        read_status=alert.read_status
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return new_alert


@router.get("/", response_model=List[schema.AlertRead])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    alerts = (
        db.query(models.Alert)
        .filter(models.Alert.user_id == current_user.id)
        .order_by(models.Alert.timestamp.desc())
        .all()
    )
    return alerts


@router.get("/{alert_id}", response_model=schema.AlertRead)
def get_alert_by_id(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    alert = (
        db.query(models.Alert)
        .filter(models.Alert.id == alert_id, models.Alert.user_id == current_user.id)
        .first()
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    alert = (
        db.query(models.Alert)
        .filter(models.Alert.id == alert_id, models.Alert.user_id == current_user.id)
        .first()
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    db.delete(alert)
    db.commit()
    return {"message": "Deleted successfully"}
@router.put("/{alert_id}/read", response_model=schema.AlertRead)
def mark_as_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id, models.Alert.user_id == current_user.id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.read_status = True
    db.commit()
    db.refresh(alert)
    return alert