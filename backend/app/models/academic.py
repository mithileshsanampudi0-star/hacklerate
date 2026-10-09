from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums import AttendanceStatus, ExamType, db_enum


class Semester(Base):
    __tablename__ = "semesters"
    __table_args__ = (UniqueConstraint("number", "academic_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int]  # 1..8
    academic_year: Mapped[str] = mapped_column(String(9))  # e.g. 2026-27
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(15), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    credits: Mapped[int]
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    semester_number: Mapped[int]


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "course_id", "semester_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), index=True)
    faculty_id: Mapped[int | None] = mapped_column(ForeignKey("faculty.id"), index=True)

    course: Mapped[Course] = relationship()
    semester: Mapped[Semester] = relationship()


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "class_date", "period"),
        Index("ix_attendance_enrollment_date", "enrollment_id", "class_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey("enrollments.id", ondelete="CASCADE"))
    class_date: Mapped[date] = mapped_column(Date)
    period: Mapped[int]
    status: Mapped[AttendanceStatus] = mapped_column(db_enum(AttendanceStatus, "attendance_status"))


class Exam(Base):
    __tablename__ = "exams"
    __table_args__ = (UniqueConstraint("course_id", "semester_id", "type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), index=True)
    type: Mapped[ExamType] = mapped_column(db_enum(ExamType, "exam_type"))
    max_marks: Mapped[float] = mapped_column(Float)
    weightage: Mapped[float] = mapped_column(Float)  # % contribution to the course total
    exam_date: Mapped[date | None] = mapped_column(Date)


class ExamMark(Base):
    __tablename__ = "exam_marks"
    __table_args__ = (UniqueConstraint("exam_id", "student_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    marks_obtained: Mapped[float] = mapped_column(Float)


class CourseResult(Base):
    """Final grade for one enrollment, written when faculty publish results."""

    __tablename__ = "course_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey("enrollments.id", ondelete="CASCADE"), unique=True)
    total_marks: Mapped[float] = mapped_column(Float)
    grade: Mapped[str] = mapped_column(String(3))
    grade_points: Mapped[float] = mapped_column(Float)


class SemesterResult(Base):
    """Cached SGPA/CGPA per student per semester; rebuilt by services.results."""

    __tablename__ = "semester_results"
    __table_args__ = (UniqueConstraint("student_id", "semester_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), index=True)
    sgpa: Mapped[float] = mapped_column(Float)
    credits_earned: Mapped[int]
    cgpa_upto: Mapped[float] = mapped_column(Float)
