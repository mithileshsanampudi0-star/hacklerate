from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums import Role, db_enum


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(db_enum(Role, "user_role"))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(120))


class Faculty(Base):
    __tablename__ = "faculty"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    emp_id: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    designation: Mapped[str] = mapped_column(String(80))

    user: Mapped[User] = relationship()
    department: Mapped[Department] = relationship()


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    roll_no: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    batch_year: Mapped[int]
    current_semester: Mapped[int]
    section: Mapped[str] = mapped_column(String(5))
    mentor_faculty_id: Mapped[int | None] = mapped_column(ForeignKey("faculty.id"), index=True)

    user: Mapped[User] = relationship()
    department: Mapped[Department] = relationship()
    mentor: Mapped[Faculty | None] = relationship()
    profile: Mapped["StudentProfile | None"] = relationship(back_populates="student", uselist=False)


class StudentProfile(Base):
    __tablename__ = "student_profile"

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), primary_key=True)
    tenth_pct: Mapped[float | None] = mapped_column(Float)
    twelfth_pct: Mapped[float | None] = mapped_column(Float)
    phone: Mapped[str | None] = mapped_column(String(20))
    dob: Mapped[date | None] = mapped_column(Date)

    student: Mapped[Student] = relationship(back_populates="profile")
