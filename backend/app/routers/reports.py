from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.db.database import get_db
from app.models.report import Report
from app.models.user import User
from app.schemas.reports import ReportCreate, ReportOut

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def create_report(
    body: ReportCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    r = Report(
        reporter_user_id=user.id,
        target_type=body.target_type,
        target_id=body.target_id,
        reason_code=body.reason_code,
        reason_text=body.reason_text,
        status="open",
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


@router.get("/me", response_model=list[ReportOut])
def my_reports(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    rows = (
        db.query(Report)
        .filter(Report.reporter_user_id == user.id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return rows
