"""Proactive notification and alert service."""

from datetime import datetime
from typing import Any
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.analytics import Notification
from app.models.identity import User


def send_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notif_type: str = "system",
    severity: str = "info",
    link_url: str | None = None,
    prevent_duplicate_hours: int = 24,
) -> Notification | None:
    """Creates a notification for a user, avoiding spamming identical notifications."""
    if prevent_duplicate_hours > 0:
        # Check if identical notification was sent recently
        recent = db.scalar(
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.title == title,
            )
            .order_by(Notification.created_at.desc())
            .limit(1)
        )
        if recent:
            # Check elapsed hours
            elapsed = (datetime.now(recent.created_at.tzinfo) - recent.created_at).total_seconds() / 3600.0
            if elapsed < prevent_duplicate_hours:
                return recent

    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notif_type,
        severity=severity,
        link_url=link_url,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def get_user_notifications(
    db: Session,
    user_id: int,
    unread_only: bool = False,
    limit: int = 30,
) -> dict[str, Any]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    rows = db.scalars(stmt.order_by(Notification.created_at.desc()).limit(limit)).all()

    unread_count = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
    ) or 0

    return {
        "unread_count": unread_count,
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "severity": n.severity,
                "is_read": n.is_read,
                "link_url": n.link_url,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in rows
        ],
    }


def mark_notification_read(db: Session, notification_id: int, user_id: int) -> bool:
    notif = db.get(Notification, notification_id)
    if notif and notif.user_id == user_id:
        notif.is_read = True
        db.commit()
        return True
    return False


def mark_all_read(db: Session, user_id: int) -> int:
    result = db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return result.rowcount
