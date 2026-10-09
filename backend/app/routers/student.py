"""Endpoints for the logged-in student. The student is always taken from the token,
never from the URL, so one student can never read another's data."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_student
from app.db import get_db
from app.models import (
    Certification,
    Enrollment,
    FeedbackForm,
    FeedbackResponse,
    HelpReply,
    HelpRequest,
    HelpStatus,
    Semester,
    Student,
)
from app.schemas import CertificationIn, FeedbackSubmitIn, HelpRequestIn, ReplyIn
from app.services import student_data as sd

router = APIRouter(prefix="/student/me", tags=["student"])


@router.get("/dashboard")
def dashboard(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return sd.dashboard(db, student)


@router.get("/profile")
def profile(student: Student = Depends(get_current_student)):
    return sd.student_info(student)


@router.get("/attendance")
def attendance(
    semester: int | None = None,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return sd.attendance_report(db, student, semester)


@router.get("/marks")
def marks(
    semester: int | None = None,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return sd.marks(db, student, semester)


@router.get("/results")
def results(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return sd.results(db, student.id)


@router.get("/assignments")
def assignments(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return sd.assignments(db, student)


@router.get("/certifications")
def certifications(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return sd.certifications(db, student.id)


@router.post("/certifications", status_code=status.HTTP_201_CREATED)
def add_certification(
    body: CertificationIn,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    if body.issue_date > date.today():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Issue date cannot be in the future")
    cert = Certification(student_id=student.id, **body.model_dump())
    db.add(cert)
    db.commit()
    return {"id": cert.id}


@router.get("/feedback-forms")
def feedback_forms(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return sd.feedback_forms(db, student)


@router.post("/feedback-forms/{form_id}", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    form_id: int,
    body: FeedbackSubmitIn,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    form = db.get(FeedbackForm, form_id)
    if form is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Form not found")
    sem_no = db.scalar(select(Semester.number).where(Semester.id == form.semester_id))
    enrolled = {
        (c, s)
        for c, s in db.execute(
            select(Enrollment.course_id, Enrollment.semester_id).where(Enrollment.student_id == student.id)
        )
    }
    if not sd.form_applies(form, student, sem_no, enrolled):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Form not found")
    today = date.today()
    if today < form.open_from:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This form is not open yet")

    answers: dict = {}
    for q in form.questions:
        value = body.answers.get(q["id"])
        if q["type"] == "rating":
            if not isinstance(value, int) or not 1 <= value <= 5:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"'{q['text']}' needs a rating from 1 to 5")
        else:
            value = (value or "").strip()[:2000] if isinstance(value, str) or value is None else str(value)
        answers[q["id"]] = value

    db.add(FeedbackResponse(form_id=form.id, student_id=student.id, answers=answers))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "You have already submitted this form")
    return {"ok": True}


@router.get("/activities")
def activities(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return sd.activities(db, student.id)


@router.get("/placement")
def placement(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return sd.placement(db, student)


@router.get("/remarks")
def remarks(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return sd.remarks(db, student.id, include_private=False)


@router.get("/courses")
def courses(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    """Current-semester courses, used to tag a help request with a course."""
    enrollments = db.scalars(
        select(Enrollment)
        .join(Semester, Semester.id == Enrollment.semester_id)
        .where(Enrollment.student_id == student.id, Semester.number == student.current_semester)
    ).all()
    return [{"id": e.course.id, "code": e.course.code, "name": e.course.name} for e in enrollments]


@router.get("/help-requests")
def help_requests(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return sd.help_requests(db, student.id)


@router.post("/help-requests", status_code=status.HTTP_201_CREATED)
def create_help_request(
    body: HelpRequestIn,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    # Route to the course teacher when a course is given, otherwise to the mentor.
    assigned = student.mentor_faculty_id
    if body.course_id is not None:
        enrollment = db.scalar(
            select(Enrollment)
            .join(Semester, Semester.id == Enrollment.semester_id)
            .where(
                Enrollment.student_id == student.id,
                Enrollment.course_id == body.course_id,
            )
            .order_by(Semester.number.desc())
            .limit(1)
        )
        if enrollment is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "You are not enrolled in that course")
        assigned = enrollment.faculty_id or assigned

    req = HelpRequest(
        student_id=student.id,
        course_id=body.course_id,
        subject=body.subject.strip(),
        message=body.message.strip(),
        status=HelpStatus.open,
        assigned_faculty_id=assigned,
    )
    db.add(req)
    db.commit()
    return {"id": req.id}


@router.post("/help-requests/{request_id}/replies", status_code=status.HTTP_201_CREATED)
def reply_help_request(
    request_id: int,
    body: ReplyIn,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    req = db.get(HelpRequest, request_id)
    if req is None or req.student_id != student.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
    if req.status == HelpStatus.resolved:
        req.status = HelpStatus.open  # a follow-up reopens the thread
    db.add(HelpReply(request_id=req.id, author_user_id=student.user_id, message=body.message.strip()))
    db.commit()
    return {"ok": True}
