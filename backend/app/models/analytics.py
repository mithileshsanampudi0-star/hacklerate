from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums import JSONType


class LMSActivity(Base):
    __tablename__ = "lms_activity"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), unique=True, index=True)
    login_count: Mapped[int] = mapped_column(Integer, default=0)
    course_views: Mapped[int] = mapped_column(Integer, default=0)
    videos_watched: Mapped[int] = mapped_column(Integer, default=0)
    assignments_completed: Mapped[int] = mapped_column(Integer, default=0)
    time_spent_hours: Mapped[float] = mapped_column(Float, default=0.0)
    last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    student = relationship("Student")


class SkillAssessment(Base):
    __tablename__ = "skill_assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    technical_score: Mapped[float] = mapped_column(Float, default=0.0)       # 0 - 100
    communication_score: Mapped[float] = mapped_column(Float, default=0.0)   # 0 - 100
    teamwork_score: Mapped[float] = mapped_column(Float, default=0.0)        # 0 - 100
    leadership_score: Mapped[float] = mapped_column(Float, default=0.0)      # 0 - 100
    problem_solving_score: Mapped[float] = mapped_column(Float, default=0.0) # 0 - 100
    aptitude_score: Mapped[float] = mapped_column(Float, default=0.0)        # 0 - 100
    mock_interview_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0 - 100
    assessment_date: Mapped[date] = mapped_column(Date)
    assessment_source: Mapped[str] = mapped_column(String(100), default="Faculty Evaluation")
    assessor_faculty_id: Mapped[int | None] = mapped_column(ForeignKey("faculty.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student")
    assessor = relationship("Faculty")


class StudentSuccessScore(Base):
    __tablename__ = "student_success_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    overall_score: Mapped[float] = mapped_column(Float)  # 0 - 100
    score_category: Mapped[str] = mapped_column(String(50))  # Excellent, Good, Average, At Risk
    cgpa_component: Mapped[float] = mapped_column(Float)
    attendance_component: Mapped[float] = mapped_column(Float)
    lms_component: Mapped[float] = mapped_column(Float)
    assignment_component: Mapped[float] = mapped_column(Float)
    certification_component: Mapped[float] = mapped_column(Float)
    placement_component: Mapped[float] = mapped_column(Float)
    feedback_component: Mapped[float] = mapped_column(Float)
    breakdown: Mapped[dict[str, Any]] = mapped_column(JSONType)  # component weights, normalized scores, contributions
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    student = relationship("Student")


class PlacementReadinessScore(Base):
    __tablename__ = "placement_readiness_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    overall_score: Mapped[float] = mapped_column(Float)  # 0 - 100
    category: Mapped[str] = mapped_column(String(50))   # Needs Improvement, Developing, Placement Ready
    coding_score: Mapped[float] = mapped_column(Float)
    aptitude_score: Mapped[float] = mapped_column(Float)
    communication_score: Mapped[float] = mapped_column(Float)
    mock_interview_score: Mapped[float] = mapped_column(Float)
    cgpa_score: Mapped[float] = mapped_column(Float)
    strengths: Mapped[list[str]] = mapped_column(JSONType, default=list)
    skill_gaps: Mapped[list[str]] = mapped_column(JSONType, default=list)
    recommendations: Mapped[list[str]] = mapped_column(JSONType, default=list)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    student = relationship("Student")


class AcademicRiskPrediction(Base):
    __tablename__ = "academic_risk_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    risk_probability: Mapped[float] = mapped_column(Float)  # 0 - 100 %
    risk_category: Mapped[str] = mapped_column(String(20))   # low, medium, high
    model_version: Mapped[str] = mapped_column(String(50))
    contributing_factors: Mapped[list[dict[str, Any]]] = mapped_column(JSONType)  # e.g. [{"factor": "Attendance", "impact": -15, "detail": "..."}, ...]
    suggested_interventions: Mapped[list[str]] = mapped_column(JSONType)
    prediction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    student = relationship("Student")


class PlacementRiskPrediction(Base):
    __tablename__ = "placement_risk_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    risk_probability: Mapped[float] = mapped_column(Float)  # 0 - 100 %
    risk_category: Mapped[str] = mapped_column(String(20))   # low, medium, high
    model_version: Mapped[str] = mapped_column(String(50))
    readiness_score: Mapped[float] = mapped_column(Float)
    key_factors: Mapped[list[str]] = mapped_column(JSONType)
    recommendations: Mapped[list[str]] = mapped_column(JSONType)
    prediction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    student = relationship("Student")


class StudentSegment(Base):
    __tablename__ = "student_segments"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    segment_code: Mapped[str] = mapped_column(String(10))  # A, B, C, D
    segment_name: Mapped[str] = mapped_column(String(100))  # Top Performers, Academically Strong Placement Weak, etc.
    assignment_reason: Mapped[str] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    student = relationship("Student")


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    faculty_id: Mapped[int | None] = mapped_column(ForeignKey("faculty.id"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(50))  # academic, placement, attendance, counseling
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    urgency: Mapped[str] = mapped_column(String(20))   # low, medium, high, critical
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, in_progress, completed, dismissed
    action_steps: Mapped[list[str]] = mapped_column(JSONType, default=list)
    student_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    faculty_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student = relationship("Student")
    faculty = relationship("Faculty")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(50))  # attendance_alert, cgpa_alert, assignment_deadline, academic_risk, placement_alert, intervention, system
    severity: Mapped[str] = mapped_column(String(20), default="info")  # info, warning, critical, success
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    link_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User")


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONType)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(100), index=True)  # academic_risk, placement_risk
    model_version: Mapped[str] = mapped_column(String(50))
    algorithm: Mapped[str] = mapped_column(String(100))
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONType)  # accuracy, precision, recall, f1, roc_auc
    feature_importances: Mapped[dict[str, float]] = mapped_column(JSONType)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
