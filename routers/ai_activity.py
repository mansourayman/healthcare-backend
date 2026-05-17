from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import sessionLocal
from .. import models
from .auth import get_current_user

router = APIRouter(prefix="/ai/activity", tags=["AI Activity"])


def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/latest")
def get_latest_ai_activity(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    scan = (
        db.query(models.HeartRateScan)
        .filter(models.HeartRateScan.user_id == current_user.id)
        .order_by(models.HeartRateScan.timestamp.desc())
        .first()
    )

    if not scan:
        raise HTTPException(status_code=404, detail="No scan data found")

    return {
        "activity": getattr(scan, "activity", "unknown"),
        "risk_level": getattr(scan, "risk_level", "normal"),
        "heart_rate": scan.heart_rate,
        "steps": scan.steps_delta,
        "jumps": scan.jumps_delta,
        "timestamp": scan.timestamp
    }
