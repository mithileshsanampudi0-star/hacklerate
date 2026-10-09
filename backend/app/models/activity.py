from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import ActivityLevel, ActivityType, SubmissionStatus, db_enum


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[date] = mapped_column(Date)
    max_marks: Mapped[float] = mapped_column(Float)


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"
    __table_args__ = (UniqueConstraint("assignment_id", "student_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    marks: Mapped[float | None] = mapped_column(Float)
    status: Mapped[SubmissionStatus] = mapped_column(db_enum(SubmissionStatus, "submission_status"))


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    issuer: Mapped[str] = mapped_column(String(120))
    issue_date: Mapped[date] = mapped_column(Date)
    credential_url: Mapped[str | None] = mapped_column(String(500))
    verified_by: Mapped[int | None] = mapped_column(ForeignKey("faculty.id"), index=True)


class Club(Base):
    __tablename__ = "clubs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    category: Mapped[str] = mapped_column(String(50))


class ClubMembership(Base):
    __tablename__ = "club_memberships"
    __table_args__ = (UniqueConstraint("student_id", "club_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id"), index=True)
    role: Mapped[str] = mapped_column(String(50), default="Member")
    joined_on: Mapped[date] = mapped_column(Date)


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    type: Mapped[ActivityType] = mapped_column(db_enum(ActivityType, "activity_type"))
    level: Mapped[ActivityLevel] = mapped_column(db_enum(ActivityLevel, "activity_level"))
    achievement: Mapped[str | None] = mapped_column(String(120))  # e.g. "Winner", "Participant"
    activity_date: Mapped[date] = mapped_column(Date)
