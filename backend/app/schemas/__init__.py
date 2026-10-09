from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.enums import AttendanceStatus, HelpStatus, RemarkCategory, RemarkVisibility


# ---------------------------------------------------------------- auth
class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)
    role: Literal["student", "faculty", "admin"]



class RefreshIn(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str


class Me(BaseModel):
    id: int
    email: str
    role: str
    name: str
    profile_id: int


# ---------------------------------------------------------------- student
class CertificationIn(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    issuer: str = Field(min_length=2, max_length=120)
    issue_date: date
    credential_url: str | None = Field(default=None, max_length=500)


class FeedbackSubmitIn(BaseModel):
    answers: dict[str, Any]


class HelpRequestIn(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    message: str = Field(min_length=1, max_length=4000)
    course_id: int | None = None


class ReplyIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


# ---------------------------------------------------------------- faculty
class RemarkIn(BaseModel):
    category: RemarkCategory
    remark: str = Field(min_length=3, max_length=4000)
    visibility: RemarkVisibility = RemarkVisibility.student


class HelpUpdateIn(BaseModel):
    status: HelpStatus | None = None
    assign_to_me: bool = False


class MarkEntry(BaseModel):
    student_id: int
    marks: float = Field(ge=0)


class MarksBulkIn(BaseModel):
    exam_id: int
    entries: list[MarkEntry]


class AttendanceEntry(BaseModel):
    student_id: int
    status: AttendanceStatus


class AttendanceBulkIn(BaseModel):
    course_id: int
    semester_id: int
    class_date: date
    period: int = Field(ge=1, le=10)
    entries: list[AttendanceEntry]


class PublishIn(BaseModel):
    course_id: int
    semester_id: int
