from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.security import get_current_faculty
from app.db import get_db
from app.models import (
    Attendance,
    Certification,
    Course,
    Enrollment,
    Exam,
    ExamMark,
    Faculty,
    FacultyRemark,
    HelpReply,
    HelpRequest,
    HelpStatus,
    Semester,
    Student,
)
from app.schemas import AttendanceBulkIn, HelpUpdateIn, MarksBulkIn, PublishIn, RemarkIn, ReplyIn
from app.services import results as results_service
from app.services import student_data as sd

router = APIRouter(prefix="/faculty", tags=["faculty"])

LOW_CGPA = 6.0


def _get_student(db: Session, student_id: int) -> Student:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    return student


def _ensure_teaches(db: Session, faculty: Faculty, course_id: int, semester_id: int) -> None:
    teaches = db.scalar(
        select(Enrollment.id)
        .where(
            Enrollment.course_id == course_id,
            Enrollment.semester_id == semester_id,
            Enrollment.faculty_id == faculty.id,
        )
        .limit(1)
    )
    if teaches is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not teach this course offering")


def _risk_reasons(o: dict) -> list[str]:
    reasons = []
    if o["attendance_risk"] == "critical":
        reasons.append(f"Attendance {o['attendance_pct']}% is below 75%")
    elif o["attendance_risk"] == "warning":
        reasons.append(f"Attendance {o['attendance_pct']}% is close to the 75% limit")
    if o["active_backlogs"]:
        reasons.append(f"{o['active_backlogs']} active backlog(s)")
    if o["cgpa"] is not None and o["cgpa"] < LOW_CGPA:
        reasons.append(f"CGPA {o['cgpa']} is below {LOW_CGPA}")
    return reasons


def _at_risk(overviews: list[dict]) -> list[dict]:
    out = []
    for o in overviews:
        reasons = _risk_reasons(o)
        if reasons:
            high = o["attendance_risk"] == "critical" or o["active_backlogs"] > 0
            out.append({**o, "reasons": reasons, "severity": "high" if high else "medium"})
    return sorted(out, key=lambda r: (r["severity"] != "high", r["attendance_pct"] or 0))


def _department_students(db: Session, faculty: Faculty) -> list[Student]:
    return list(
        db.scalars(
            select(Student).where(Student.department_id == faculty.department_id).order_by(Student.roll_no)
        )
    )


@router.get("/dashboard")
def dashboard(faculty: Faculty = Depends(get_current_faculty), db: Session = Depends(get_db)):
    overviews = [sd.overview(db, s) for s in _department_students(db, faculty)]
    cgpas = [o["cgpa"] for o in overviews if o["cgpa"] is not None]
    buckets = {"< 6": 0, "6–7": 0, "7–8": 0, "8–9": 0, "9+": 0}
    for c in cgpas:
        key = "< 6" if c < 6 else "6–7" if c < 7 else "7–8" if c < 8 else "8–9" if c < 9 else "9+"
        buckets[key] += 1

    open_help = db.scalar(
        select(func.count(HelpRequest.id)).where(
            HelpRequest.status != HelpStatus.resolved,
            or_(HelpRequest.assigned_faculty_id == faculty.id, HelpRequest.assigned_faculty_id.is_(None)),
        )
    )
    return {
        "faculty": {
            "id": faculty.id,
            "name": faculty.name,
            "designation": faculty.designation,
            "department": faculty.department.name,
        },
        "total_students": len(overviews),
        "my_mentees": sum(1 for o in overviews if o["mentor_faculty_id"] == faculty.id),
        "average_cgpa": round(sum(cgpas) / len(cgpas), 2) if cgpas else None,
        "attendance_critical": sum(1 for o in overviews if o["attendance_risk"] == "critical"),
        "attendance_warning": sum(1 for o in overviews if o["attendance_risk"] == "warning"),
        "with_backlogs": sum(1 for o in overviews if o["active_backlogs"]),
        "placement_eligible": sum(1 for o in overviews if o["placement_eligible"]),
        "open_help_requests": open_help,
        "cgpa_distribution": [{"range": k, "students": v} for k, v in buckets.items()],
        "at_risk": _at_risk(overviews)[:8],
    }


@router.get("/students")
def list_students(
    search: str | None = None,
    semester: int | None = None,
    section: str | None = None,
    risk: str | None = Query(default=None, pattern="^(safe|warning|critical|any)$"),
    mentees_only: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db),
):
    stmt = select(Student).where(Student.department_id == faculty.department_id)
    if search:
        like = f"%{search.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(Student.name).like(like), func.lower(Student.roll_no).like(like)))
    if semester:
        stmt = stmt.where(Student.current_semester == semester)
    if section:
        stmt = stmt.where(Student.section == section)
    if mentees_only:
        stmt = stmt.where(Student.mentor_faculty_id == faculty.id)

    overviews = [sd.overview(db, s) for s in db.scalars(stmt.order_by(Student.roll_no))]
    if risk == "any":
        overviews = [o for o in overviews if _risk_reasons(o)]
    elif risk:
        overviews = [o for o in overviews if o["attendance_risk"] == risk]

    start = (page - 1) * page_size
    return {"items": overviews[start : start + page_size], "total": len(overviews), "page": page, "page_size": page_size}


@router.get("/at-risk")
def at_risk(faculty: Faculty = Depends(get_current_faculty), db: Session = Depends(get_db)):
    return _at_risk([sd.overview(db, s) for s in _department_students(db, faculty)])


@router.get("/students/{student_id}")
def student_detail(student_id: int, faculty: Faculty = Depends(get_current_faculty), db: Session = Depends(get_db)):
    return sd.full_profile(db, _get_student(db, student_id))


@router.post("/students/{student_id}/remarks", status_code=status.HTTP_201_CREATED)
def add_remark(
    student_id: int,
    body: RemarkIn,
    faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db),
):
    _get_student(db, student_id)
    remark = FacultyRemark(
        student_id=student_id,
        faculty_id=faculty.id,
        category=body.category,
        remark=body.remark.strip(),
        visibility=body.visibility,
    )
    db.add(remark)
    db.commit()
    return {"id": remark.id}


# ---------------------------------------------------------------- help requests
@router.get("/help-requests")
def help_requests(
    status_filter: HelpStatus | None = Query(default=None, alias="status"),
    scope: str = Query(default="mine", pattern="^(mine|all)$"),
    faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db),
):
    stmt = select(HelpRequest).order_by(HelpRequest.created_at.desc())
    if scope == "mine":
        stmt = stmt.where(
            or_(HelpRequest.assigned_faculty_id == faculty.id, HelpRequest.assigned_faculty_id.is_(None))
        )
    if status_filter:
        stmt = stmt.where(HelpRequest.status == status_filter)
    return sd.serialize_help_requests(db, list(db.scalars(stmt)))


def _get_help_request(db: Session, request_id: int) -> HelpRequest:
    req = db.get(HelpRequest, request_id)
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
    return req


@router.post("/help-requests/{request_id}/replies", status_code=status.HTTP_201_CREATED)
def reply_help_request(
    request_id: int,
    body: ReplyIn,
    faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db),
):
    req = _get_help_request(db, request_id)
    if req.assigned_faculty_id is None:
        req.assigned_faculty_id = faculty.id
    if req.status == HelpStatus.open:
        req.status = HelpStatus.in_progress
    db.add(HelpReply(request_id=req.id, author_user_id=faculty.user_id, message=body.message.strip()))
    db.commit()
    return {"ok": True}


@router.patch("/help-requests/{request_id}")
def update_help_request(
    request_id: int,
    body: HelpUpdateIn,
    faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db),
):
    req = _get_help_request(db, request_id)
    if body.assign_to_me:
        req.assigned_faculty_id = faculty.id
    if body.status is not None:
        req.status = body.status
    db.commit()
    return {"ok": True, "status": req.status.value}


# ---------------------------------------------------------------- data entry
@router.get("/courses")
def my_courses(faculty: Faculty = Depends(get_current_faculty), db: Session = Depends(get_db)):
    """Course offerings this faculty teaches, with their exams (ids needed for marks entry)."""
    rows = db.execute(
        select(Course, Semester, func.count(Enrollment.id))
        .join(Enrollment, Enrollment.course_id == Course.id)
        .join(Semester, Semester.id == Enrollment.semester_id)
        .where(Enrollment.faculty_id == faculty.id)
        .group_by(Course.id, Semester.id)
        .order_by(Semester.number.desc(), Course.code)
    ).all()
    exams = db.scalars(select(Exam)).all()
    return [
        {
            "course_id": c.id,
            "code": c.code,
            "name": c.name,
            "semester_id": s.id,
            "semester": s.number,
            "academic_year": s.academic_year,
            "students": n,
            "exams": [
                {"id": e.id, "type": e.type.value, "max_marks": e.max_marks, "exam_date": e.exam_date}
                for e in exams
                if e.course_id == c.id and e.semester_id == s.id
            ],
        }
        for c, s, n in rows
    ]


@router.post("/marks")
def enter_marks(body: MarksBulkIn, faculty: Faculty = Depends(get_current_faculty), db: Session = Depends(get_db)):
    exam = db.get(Exam, body.exam_id)
    if exam is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam not found")
    _ensure_teaches(db, faculty, exam.course_id, exam.semester_id)

    enrolled = set(
        db.scalars(
            select(Enrollment.student_id).where(
                Enrollment.course_id == exam.course_id, Enrollment.semester_id == exam.semester_id
            )
        )
    )
    existing = {m.student_id: m for m in db.scalars(select(ExamMark).where(ExamMark.exam_id == exam.id))}
    for entry in body.entries:
        if entry.student_id not in enrolled:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Student {entry.student_id} is not enrolled")
        if entry.marks > exam.max_marks:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Marks cannot exceed {exam.max_marks}")
        row = existing.get(entry.student_id) or ExamMark(exam_id=exam.id, student_id=entry.student_id)
        row.marks_obtained = entry.marks
        db.add(row)
    db.commit()
    return {"saved": len(body.entries)}


@router.post("/attendance")
def mark_attendance(
    body: AttendanceBulkIn, faculty: Faculty = Depends(get_current_faculty), db: Session = Depends(get_db)
):
    _ensure_teaches(db, faculty, body.course_id, body.semester_id)
    enrollments = {
        e.student_id: e
        for e in db.scalars(
            select(Enrollment).where(
                Enrollment.course_id == body.course_id, Enrollment.semester_id == body.semester_id
            )
        )
    }
    existing = {
        a.enrollment_id: a
        for a in db.scalars(
            select(Attendance).where(
                Attendance.enrollment_id.in_([e.id for e in enrollments.values()]),
                Attendance.class_date == body.class_date,
                Attendance.period == body.period,
            )
        )
    }
    for entry in body.entries:
        enrollment = enrollments.get(entry.student_id)
        if enrollment is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Student {entry.student_id} is not enrolled")
        row = existing.get(enrollment.id) or Attendance(
            enrollment_id=enrollment.id, class_date=body.class_date, period=body.period
        )
        row.status = entry.status
        db.add(row)
    db.commit()
    return {"saved": len(body.entries)}


@router.post("/results/publish")
def publish_results(body: PublishIn, faculty: Faculty = Depends(get_current_faculty), db: Session = Depends(get_db)):
    _ensure_teaches(db, faculty, body.course_id, body.semester_id)
    count = results_service.publish_course_results(db, body.course_id, body.semester_id)
    db.commit()
    return {"published": count}


@router.post("/certifications/{cert_id}/verify")
def verify_certification(cert_id: int, faculty: Faculty = Depends(get_current_faculty), db: Session = Depends(get_db)):
    cert = db.get(Certification, cert_id)
    if cert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Certification not found")
    cert.verified_by = faculty.id
    db.commit()
    return {"ok": True}
