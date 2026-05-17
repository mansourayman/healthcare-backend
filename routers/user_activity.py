from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models, schema
from database import sessionLocal
from .auth import get_current_user

router = APIRouter(prefix="/activity", tags=["User Activity"])


def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schema.UserActivityRead)
def add_or_update_activity(
    activity: schema.UserActivityCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if activity.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    
    existing_activity = db.query(models.UserActivity).filter(
        models.UserActivity.user_id == current_user.id,
        models.UserActivity.date == activity.date
    ).first()

    if existing_activity:
        
        existing_activity.sleep_start = activity.sleep_start
        existing_activity.sleep_end = activity.sleep_end
        existing_activity.activity_level = activity.activity_level
        existing_activity.notes = activity.notes
        db.commit()
        db.refresh(existing_activity)
        return existing_activity
    else:
        
        new_activity = models.UserActivity(
            user_id=activity.user_id,
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
def get_all_activities(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    activities = db.query(models.UserActivity).filter(
        models.UserActivity.user_id == current_user.id
    ).order_by(models.UserActivity.date.desc()).all()
    return activities


@router.get("/{date}", response_model=schema.UserActivityRead)
def get_activity_by_date(
    date: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    activity = db.query(models.UserActivity).filter(
        models.UserActivity.user_id == current_user.id,
        models.UserActivity.date == date
    ).first()
    if not activity:
        raise HTTPException(status_code=404, detail="No activity found for this date")
    return activity


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    activity = db.query(models.UserActivity).filter(
        models.UserActivity.id == activity_id,
        models.UserActivity.user_id == current_user.id
    ).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    db.delete(activity)
    db.commit()
    return {"detail": "Activity deleted successfully"}
