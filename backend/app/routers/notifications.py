"""Notifications Router: User alerts, notification center, and read acknowledgments."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db import get_db
from app.models.identity import User
from app.services.notifications import get_user_notifications, mark_all_read, mark_notification_read

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=30, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_user_notifications(db, user.id, unread_only=unread_only, limit=limit)


@router.patch("/{notification_id}/read")
def mark_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ok = mark_notification_read(db, notification_id, user.id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    return {"message": "Notification marked as read"}


@router.post("/read-all")
def mark_all_as_read(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = mark_all_read(db, user.id)
    return {"message": f"{count} notification(s) marked as read"}
