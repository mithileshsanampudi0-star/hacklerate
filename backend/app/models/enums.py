import enum

from sqlalchemy import JSON, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB

# JSONB on Postgres, plain JSON elsewhere (SQLite in tests)
JSONType = JSON().with_variant(JSONB(), "postgresql")


def db_enum(cls: type[enum.Enum], name: str) -> SAEnum:
    """Native Postgres enum that stores the lowercase .value, not the member name."""
    return SAEnum(cls, name=name, values_callable=lambda e: [m.value for m in e])


class Role(str, enum.Enum):
    student = "student"
    faculty = "faculty"
    admin = "admin"


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    od = "od"  # on-duty (college event), counts as present
    medical = "medical"  # approved medical leave, counts as present


class ExamType(str, enum.Enum):
    internal1 = "internal1"
    internal2 = "internal2"
    assignment = "assignment"
    lab = "lab"
    end_sem = "end_sem"


class SubmissionStatus(str, enum.Enum):
    pending = "pending"
    submitted = "submitted"
    late = "late"
    graded = "graded"


class ActivityType(str, enum.Enum):
    event = "event"
    competition = "competition"
    hackathon = "hackathon"
    sports = "sports"
    cultural = "cultural"
    nss = "nss"


class ActivityLevel(str, enum.Enum):
    college = "college"
    state = "state"
    national = "national"


class RemarkCategory(str, enum.Enum):
    behaviour = "behaviour"
    academic = "academic"
    attendance = "attendance"
    appreciation = "appreciation"


class RemarkVisibility(str, enum.Enum):
    student = "student"
    faculty_only = "faculty_only"


class HelpStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
