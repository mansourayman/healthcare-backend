from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models
import schema
from database import sessionLocal
from routers.auth import get_current_user
from datetime import date

router = APIRouter(prefix="/activity", tags=["User Activity"])

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schema.UserActivityRead, status_code=status.HTTP_201_CREATED)
def create_activity(
    activity: schema.UserActivityCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    ينشئ نشاط يومي (UserActivity). لا يعتمد على user_id من الطلب،
    بل يستخدم المستخدم الحالي (current_user).
    """
    new_activity = models.UserActivity(
        user_id=current_user.id,
        date=activity.date,
        sleep_start=activity.sleep_start,
        sleep_end=activity.sleep_end,
        activity_level=activity.activity_level,
        notes=activity.notes
    )
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    return new_activity


@router.get("/", response_model=List[schema.UserActivityRead])
def get_user_activity(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    يرجع كل النشاطات للمستخدم الحالي، مرتبة تنازلياً حسب التاريخ.
    """
    activities = (
        db.query(models.UserActivity)
        .filter(models.UserActivity.user_id == current_user.id)
        .order_by(models.UserActivity.date.desc())
        .all()
    )
    return activities


@router.get("/{activity_id}", response_model=schema.UserActivityRead)
def get_activity_by_id(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    activity = (
        db.query(models.UserActivity)
        .filter(models.UserActivity.id == activity_id, models.UserActivity.user_id == current_user.id)
        .first()
    )
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    activity = (
        db.query(models.UserActivity)
        .filter(models.UserActivity.id == activity_id, models.UserActivity.user_id == current_user.id)
        .first()
    )
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    db.delete(activity)
    db.commit()
    return {"message": "Deleted successfully"}
