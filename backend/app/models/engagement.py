from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import HelpStatus, JSONType, RemarkCategory, RemarkVisibility, db_enum


class FeedbackForm(Base):
    """A form students must fill. Course-specific when course_id is set, otherwise
    it applies to every student of the department (or all departments) in that semester."""

    __tablename__ = "feedback_forms"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"), index=True)
    faculty_id: Mapped[int | None] = mapped_column(ForeignKey("faculty.id"), index=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), index=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), index=True)
    open_from: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    # [{"id": "q1", "text": "...", "type": "rating" | "text"}]
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSONType)


class FeedbackResponse(Base):
    __tablename__ = "feedback_responses"
    __table_args__ = (UniqueConstraint("form_id", "student_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("feedback_forms.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    answers: Mapped[dict[str, Any]] = mapped_column(JSONType)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FacultyRemark(Base):
    __tablename__ = "faculty_remarks"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculty.id"), index=True)
    category: Mapped[RemarkCategory] = mapped_column(db_enum(RemarkCategory, "remark_category"))
    remark: Mapped[str] = mapped_column(Text)
    visibility: Mapped[RemarkVisibility] = mapped_column(db_enum(RemarkVisibility, "remark_visibility"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HelpRequest(Base):
    __tablename__ = "help_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"), index=True)
    subject: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[HelpStatus] = mapped_column(db_enum(HelpStatus, "help_status"), default=HelpStatus.open)
    assigned_faculty_id: Mapped[int | None] = mapped_column(ForeignKey("faculty.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HelpReply(Base):
    __tablename__ = "help_replies"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("help_requests.id", ondelete="CASCADE"), index=True)
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PlacementCriteria(Base):
    __tablename__ = "placement_criteria"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_year: Mapped[int] = mapped_column(unique=True)
    min_cgpa: Mapped[float] = mapped_column(Float)
    max_active_backlogs: Mapped[int]
    min_attendance_pct: Mapped[float] = mapped_column(Float)
    min_10th_pct: Mapped[float] = mapped_column(Float)
    min_12th_pct: Mapped[float] = mapped_column(Float)
