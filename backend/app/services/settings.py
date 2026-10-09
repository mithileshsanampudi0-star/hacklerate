"""Configurable system settings for scoring weights and thresholds."""

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analytics import SystemSetting

DEFAULT_SUCCESS_SCORE_WEIGHTS = {
    "cgpa": 0.30,
    "attendance": 0.20,
    "lms": 0.15,
    "assignments": 0.10,
    "certifications": 0.10,
    "placement": 0.10,
    "feedback": 0.05,
}

DEFAULT_PLACEMENT_READINESS_WEIGHTS = {
    "coding": 0.30,
    "aptitude": 0.20,
    "communication": 0.15,
    "mock_interview": 0.15,
    "cgpa": 0.20,
}

DEFAULT_THRESHOLDS = {
    "attendance_minimum": 75.0,
    "attendance_safe": 85.0,
    "cgpa_low": 6.0,
    "academic_risk_high": 65.0,
    "academic_risk_medium": 35.0,
    "placement_ready_score": 75.0,
    "placement_developing_score": 55.0,
}


def get_setting(db: Session, key: str, default: dict[str, Any]) -> dict[str, Any]:
    row = db.scalar(select(SystemSetting).where(SystemSetting.key == key))
    if row and row.value:
        return {**default, **row.value}
    return default


def set_setting(db: Session, key: str, value: dict[str, Any]) -> dict[str, Any]:
    row = db.scalar(select(SystemSetting).where(SystemSetting.key == key))
    if row:
        row.value = value
    else:
        row = SystemSetting(key=key, value=value)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row.value


def get_success_score_weights(db: Session) -> dict[str, float]:
    return get_setting(db, "success_score_weights", DEFAULT_SUCCESS_SCORE_WEIGHTS)


def get_placement_weights(db: Session) -> dict[str, float]:
    return get_setting(db, "placement_readiness_weights", DEFAULT_PLACEMENT_READINESS_WEIGHTS)


def get_thresholds(db: Session) -> dict[str, float]:
    return get_setting(db, "thresholds", DEFAULT_THRESHOLDS)
