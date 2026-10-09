"""Read-side queries that build a student's academic picture.

Both the student router (/student/me/...) and the faculty router (/faculty/students/{id})
call these, so a student and their faculty always see identical numbers.
"""

from collections import defaultdict
from datetime import date

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.models import (
    Activity,
    Assignment,
    AssignmentSubmission,
    Attendance,
    AttendanceStatus,
    Certification,
    Club,
    ClubMembership,
    Course,
    CourseResult,
    Enrollment,
    Exam,
    ExamMark,
    Faculty,
    FacultyRemark,
    FeedbackForm,
    FeedbackResponse,
    HelpReply,
    HelpRequest,
    PlacementCriteria,
    RemarkVisibility,
    Semester,
    Student,
)
from app.services import attendance as att
from app.services import gpa
from app.services import placement as plc

PRESENT_STATUSES = [AttendanceStatus.present, AttendanceStatus.od, AttendanceStatus.medical]


def student_info(student: Student) -> dict:
    return {
        "id": student.id,
        "roll_no": student.roll_no,
        "name": student.name,
        "email": student.user.email,
        "department": student.department.name,
        "batch_year": student.batch_year,
        "current_semester": student.current_semester,
        "section": student.section,
        "mentor": student.mentor.name if student.mentor else None,
    }


# ---------------------------------------------------------------- grades
def results(db: Session, student_id: int) -> dict:
    rows = db.execute(
        select(
            Semester.number.label("semester"),
            Course.id.label("course_id"),
            Course.code,
            Course.name,
            Course.credits,
            CourseResult.grade,
            CourseResult.grade_points,
            CourseResult.total_marks,
        )
        .select_from(CourseResult)
        .join(Enrollment, Enrollment.id == CourseResult.enrollment_id)
        .join(Course, Course.id == Enrollment.course_id)
        .join(Semester, Semester.id == Enrollment.semester_id)
        .where(Enrollment.student_id == student_id)
        .order_by(Semester.number, Course.code)
    ).all()

    summary = gpa.summarize(gpa.CourseGrade(r.semester, r.course_id, r.credits, r.grade_points) for r in rows)
    by_sem: dict[int, list] = defaultdict(list)
    for r in rows:
        by_sem[r.semester].append(
            {
                "code": r.code,
                "name": r.name,
                "credits": r.credits,
                "grade": r.grade,
                "grade_points": r.grade_points,
                "total_marks": r.total_marks,
            }
        )
    for s in summary["semesters"]:
        s["courses"] = by_sem[s["semester"]]
    return summary


# ---------------------------------------------------------------- attendance
def attendance_report(db: Session, student: Student, semester_number: int | None = None) -> dict:
    number = semester_number or student.current_semester
    attended_expr = func.coalesce(func.sum(case((Attendance.status.in_(PRESENT_STATUSES), 1), else_=0)), 0)
    rows = db.execute(
        select(
            Course.id.label("course_id"),
            Course.code,
            Course.name,
            func.count(Attendance.id).label("total"),
            attended_expr.label("attended"),
        )
        .select_from(Enrollment)
        .join(Course, Course.id == Enrollment.course_id)
        .join(Semester, Semester.id == Enrollment.semester_id)
        .outerjoin(Attendance, Attendance.enrollment_id == Enrollment.id)
        .where(Enrollment.student_id == student.id, Semester.number == number)
        .group_by(Course.id, Course.code, Course.name)
        .order_by(Course.code)
    ).all()

    courses = [
        {"course_id": r.course_id, "code": r.code, "name": r.name, **att.summarize(int(r.attended), int(r.total))}
        for r in rows
    ]
    overall = att.summarize(sum(c["attended"] for c in courses), sum(c["total"] for c in courses))

    absences = db.execute(
        select(Attendance.class_date, Attendance.period, Course.code)
        .join(Enrollment, Enrollment.id == Attendance.enrollment_id)
        .join(Course, Course.id == Enrollment.course_id)
        .join(Semester, Semester.id == Enrollment.semester_id)
        .where(
            Enrollment.student_id == student.id,
            Semester.number == number,
            Attendance.status == AttendanceStatus.absent,
        )
        .order_by(Attendance.class_date.desc(), Attendance.period.desc())
        .limit(10)
    ).all()

    return {
        "semester": number,
        "overall": overall,
        "courses": courses,
        "courses_at_risk": sum(1 for c in courses if c["risk"] != "safe"),
        "recent_absences": [{"date": a.class_date, "period": a.period, "code": a.code} for a in absences],
    }


# ---------------------------------------------------------------- marks
def marks(db: Session, student: Student, semester_number: int | None = None) -> list[dict]:
    stmt = (
        select(
            Semester.number.label("semester"),
            Course.id.label("course_id"),
            Course.code,
            Course.name,
            Exam.id.label("exam_id"),
            Exam.type,
            Exam.max_marks,
            Exam.weightage,
            Exam.exam_date,
            ExamMark.marks_obtained,
        )
        .select_from(Exam)
        .join(
            Enrollment,
            and_(
                Enrollment.course_id == Exam.course_id,
                Enrollment.semester_id == Exam.semester_id,
                Enrollment.student_id == student.id,
            ),
        )
        .join(Course, Course.id == Exam.course_id)
        .join(Semester, Semester.id == Exam.semester_id)
        .outerjoin(ExamMark, and_(ExamMark.exam_id == Exam.id, ExamMark.student_id == student.id))
        .order_by(Semester.number.desc(), Course.code, Exam.exam_date)
    )
    if semester_number:
        stmt = stmt.where(Semester.number == semester_number)

    grades = {
        (sem, cid): (grade, total)
        for sem, cid, grade, total in db.execute(
            select(Semester.number, Enrollment.course_id, CourseResult.grade, CourseResult.total_marks)
            .join(Enrollment, Enrollment.id == CourseResult.enrollment_id)
            .join(Semester, Semester.id == Enrollment.semester_id)
            .where(Enrollment.student_id == student.id)
        )
    }

    sems: dict[int, dict[int, dict]] = defaultdict(dict)
    for r in db.execute(stmt):
        course = sems[r.semester].setdefault(
            r.course_id,
            {
                "course_id": r.course_id,
                "code": r.code,
                "name": r.name,
                "exams": [],
                "grade": grades.get((r.semester, r.course_id), (None, None))[0],
                "total_marks": grades.get((r.semester, r.course_id), (None, None))[1],
            },
        )
        course["exams"].append(
            {
                "exam_id": r.exam_id,
                "type": r.type.value,
                "max_marks": r.max_marks,
                "weightage": r.weightage,
                "exam_date": r.exam_date,
                "marks": r.marks_obtained,
                "percentage": round(100 * r.marks_obtained / r.max_marks, 1)
                if r.marks_obtained is not None
                else None,
            }
        )
    return [{"semester": s, "courses": list(courses.values())} for s, courses in sems.items()]


# ---------------------------------------------------------------- assignments
def assignments(db: Session, student: Student) -> dict:
    rows = db.execute(
        select(Assignment, Course.code, Course.name, AssignmentSubmission)
        .join(Course, Course.id == Assignment.course_id)
        .join(Semester, Semester.id == Assignment.semester_id)
        .join(
            Enrollment,
            and_(
                Enrollment.course_id == Assignment.course_id,
                Enrollment.semester_id == Assignment.semester_id,
                Enrollment.student_id == student.id,
            ),
        )
        .outerjoin(
            AssignmentSubmission,
            and_(
                AssignmentSubmission.assignment_id == Assignment.id,
                AssignmentSubmission.student_id == student.id,
            ),
        )
        .where(Semester.number == student.current_semester)
        .order_by(Assignment.due_date)
    ).all()

    today = date.today()
    items = []
    for a, code, name, sub in rows:
        if sub is not None and sub.status.value != "pending":
            status = sub.status.value
        else:
            status = "overdue" if a.due_date < today else "pending"
        items.append(
            {
                "id": a.id,
                "title": a.title,
                "description": a.description,
                "course_code": code,
                "course_name": name,
                "due_date": a.due_date,
                "max_marks": a.max_marks,
                "marks": sub.marks if sub else None,
                "submitted_at": sub.submitted_at if sub else None,
                "status": status,
            }
        )
    return {
        "items": items,
        "pending": sum(1 for i in items if i["status"] == "pending"),
        "overdue": sum(1 for i in items if i["status"] == "overdue"),
    }


# ---------------------------------------------------------------- feedback forms
def form_applies(form: FeedbackForm, student: Student, semester_number: int, enrolled: set[tuple[int, int]]) -> bool:
    if form.course_id is not None:
        return (form.course_id, form.semester_id) in enrolled
    if form.department_id is not None and form.department_id != student.department_id:
        return False
    return semester_number == student.current_semester


def feedback_forms(db: Session, student: Student) -> dict:
    enrolled = {
        (c, s)
        for c, s in db.execute(
            select(Enrollment.course_id, Enrollment.semester_id).where(Enrollment.student_id == student.id)
        )
    }
    forms = db.execute(
        select(FeedbackForm, Semester.number, Course.code, Faculty.name)
        .join(Semester, Semester.id == FeedbackForm.semester_id)
        .outerjoin(Course, Course.id == FeedbackForm.course_id)
        .outerjoin(Faculty, Faculty.id == FeedbackForm.faculty_id)
        .where(Semester.number == student.current_semester)
        .order_by(FeedbackForm.due_date)
    ).all()
    responses = {
        r.form_id: r
        for r in db.scalars(select(FeedbackResponse).where(FeedbackResponse.student_id == student.id))
    }

    today = date.today()
    pending, completed = [], []
    for form, sem_no, course_code, faculty_name in forms:
        if not form_applies(form, student, sem_no, enrolled):
            continue
        item = {
            "id": form.id,
            "title": form.title,
            "course_code": course_code,
            "faculty": faculty_name,
            "open_from": form.open_from,
            "due_date": form.due_date,
            "questions": form.questions,
        }
        if form.id in responses:
            completed.append({**item, "submitted_at": responses[form.id].submitted_at})
        elif form.open_from <= today:
            pending.append({**item, "overdue": form.due_date < today})
    return {"pending": pending, "completed": completed}


# ---------------------------------------------------------------- profile extras
def certifications(db: Session, student_id: int) -> list[dict]:
    rows = db.execute(
        select(Certification, Faculty.name)
        .outerjoin(Faculty, Faculty.id == Certification.verified_by)
        .where(Certification.student_id == student_id)
        .order_by(Certification.issue_date.desc())
    ).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "issuer": c.issuer,
            "issue_date": c.issue_date,
            "credential_url": c.credential_url,
            "verified": c.verified_by is not None,
            "verified_by": verifier,
        }
        for c, verifier in rows
    ]


def activities(db: Session, student_id: int) -> dict:
    memberships = db.execute(
        select(ClubMembership, Club)
        .join(Club, Club.id == ClubMembership.club_id)
        .where(ClubMembership.student_id == student_id)
        .order_by(ClubMembership.joined_on)
    ).all()
    acts = db.execute(
        select(Activity, Club.name)
        .outerjoin(Club, Club.id == Activity.club_id)
        .where(Activity.student_id == student_id)
        .order_by(Activity.activity_date.desc())
    ).all()
    return {
        "clubs": [
            {"club": c.name, "category": c.category, "role": m.role, "joined_on": m.joined_on}
            for m, c in memberships
        ],
        "activities": [
            {
                "id": a.id,
                "title": a.title,
                "type": a.type.value,
                "level": a.level.value,
                "achievement": a.achievement,
                "date": a.activity_date,
                "club": club_name,
            }
            for a, club_name in acts
        ],
    }


def remarks(db: Session, student_id: int, include_private: bool) -> list[dict]:
    stmt = (
        select(FacultyRemark, Faculty.name)
        .join(Faculty, Faculty.id == FacultyRemark.faculty_id)
        .where(FacultyRemark.student_id == student_id)
        .order_by(FacultyRemark.created_at.desc())
    )
    if not include_private:
        stmt = stmt.where(FacultyRemark.visibility == RemarkVisibility.student)
    return [
        {
            "id": r.id,
            "category": r.category.value,
            "remark": r.remark,
            "visibility": r.visibility.value,
            "faculty": name,
            "created_at": r.created_at,
        }
        for r, name in db.execute(stmt)
    ]


def _author_names(db: Session, user_ids: set[int]) -> dict[int, str]:
    if not user_ids:
        return {}
    names = dict(db.execute(select(Student.user_id, Student.name).where(Student.user_id.in_(user_ids))).all())
    names |= dict(db.execute(select(Faculty.user_id, Faculty.name).where(Faculty.user_id.in_(user_ids))).all())
    return names


def serialize_help_requests(db: Session, requests: list[HelpRequest]) -> list[dict]:
    if not requests:
        return []
    ids = [r.id for r in requests]
    replies = db.scalars(select(HelpReply).where(HelpReply.request_id.in_(ids)).order_by(HelpReply.created_at)).all()
    student_users = dict(
        db.execute(
            select(Student.id, Student.user_id).where(Student.id.in_({r.student_id for r in requests}))
        ).all()
    )
    names = _author_names(db, {r.author_user_id for r in replies} | set(student_users.values()))
    faculty_names = dict(db.execute(select(Faculty.id, Faculty.name)).all())
    course_codes = dict(db.execute(select(Course.id, Course.code)).all())

    by_request: dict[int, list] = defaultdict(list)
    for rep in replies:
        by_request[rep.request_id].append(
            {
                "id": rep.id,
                "author": names.get(rep.author_user_id, "Unknown"),
                "author_is_student": rep.author_user_id in student_users.values(),
                "message": rep.message,
                "created_at": rep.created_at,
            }
        )
    return [
        {
            "id": r.id,
            "student_id": r.student_id,
            "student_name": names.get(student_users.get(r.student_id)),
            "subject": r.subject,
            "message": r.message,
            "course_code": course_codes.get(r.course_id),
            "status": r.status.value,
            "assigned_to": faculty_names.get(r.assigned_faculty_id),
            "assigned_faculty_id": r.assigned_faculty_id,
            "created_at": r.created_at,
            "replies": by_request[r.id],
        }
        for r in requests
    ]


def help_requests(db: Session, student_id: int) -> list[dict]:
    reqs = db.scalars(
        select(HelpRequest).where(HelpRequest.student_id == student_id).order_by(HelpRequest.created_at.desc())
    ).all()
    return serialize_help_requests(db, list(reqs))


# ---------------------------------------------------------------- placement
def placement(db: Session, student: Student, res: dict | None = None, attendance: dict | None = None) -> dict:
    res = res or results(db, student.id)
    attendance = attendance or attendance_report(db, student)
    row = db.scalar(select(PlacementCriteria).where(PlacementCriteria.batch_year == student.batch_year))
    criteria = (
        plc.Criteria(
            row.min_cgpa, row.max_active_backlogs, row.min_attendance_pct, row.min_10th_pct, row.min_12th_pct
        )
        if row
        else None
    )
    profile = student.profile
    return plc.evaluate(
        criteria,
        cgpa=res["cgpa"],
        active_backlogs=res["active_backlogs"],
        attendance_pct=attendance["overall"]["percentage"],
        tenth_pct=profile.tenth_pct if profile else None,
        twelfth_pct=profile.twelfth_pct if profile else None,
    )


# ---------------------------------------------------------------- composites
def dashboard(db: Session, student: Student) -> dict:
    res = results(db, student.id)
    attendance = attendance_report(db, student)
    forms = feedback_forms(db, student)
    assigns = assignments(db, student)
    place = placement(db, student, res, attendance)
    last_sem = res["semesters"][-1] if res["semesters"] else None
    return {
        "student": student_info(student),
        "cgpa": res["cgpa"],
        "last_sgpa": last_sem["sgpa"] if last_sem else None,
        "last_sgpa_semester": last_sem["semester"] if last_sem else None,
        "active_backlogs": res["active_backlogs"],
        "credits_earned": res["credits_earned"],
        "attendance": attendance["overall"],
        "courses_at_risk": attendance["courses_at_risk"],
        "pending_feedback": len(forms["pending"]),
        "pending_assignments": assigns["pending"] + assigns["overdue"],
        "placement_eligible": place["eligible"],
        "sgpa_trend": [{"semester": s["semester"], "sgpa": s["sgpa"], "cgpa": s["cgpa_upto"]} for s in res["semesters"]],
        "attendance_by_course": [
            {"code": c["code"], "percentage": c["percentage"], "risk": c["risk"]} for c in attendance["courses"]
        ],
        "upcoming_assignments": [a for a in assigns["items"] if a["status"] in ("pending", "overdue")][:4],
        "recent_remarks": remarks(db, student.id, include_private=False)[:2],
    }


def overview(db: Session, student: Student) -> dict:
    """Compact row for the faculty student list."""
    res = results(db, student.id)
    attendance = attendance_report(db, student)
    place = placement(db, student, res, attendance)
    return {
        "id": student.id,
        "roll_no": student.roll_no,
        "name": student.name,
        "section": student.section,
        "current_semester": student.current_semester,
        "mentor_faculty_id": student.mentor_faculty_id,
        "cgpa": res["cgpa"],
        "last_sgpa": res["semesters"][-1]["sgpa"] if res["semesters"] else None,
        "attendance_pct": attendance["overall"]["percentage"],
        "attendance_risk": attendance["overall"]["risk"],
        "courses_at_risk": attendance["courses_at_risk"],
        "active_backlogs": res["active_backlogs"],
        "placement_eligible": place["eligible"],
    }


def full_profile(db: Session, student: Student) -> dict:
    """Everything a faculty member sees on the student detail page."""
    res = results(db, student.id)
    attendance = attendance_report(db, student)
    return {
        "student": student_info(student),
        "profile": {
            "tenth_pct": student.profile.tenth_pct if student.profile else None,
            "twelfth_pct": student.profile.twelfth_pct if student.profile else None,
            "phone": student.profile.phone if student.profile else None,
        },
        "results": res,
        "attendance": attendance,
        "marks": marks(db, student),
        "assignments": assignments(db, student),
        "certifications": certifications(db, student.id),
        "activities": activities(db, student.id),
        "feedback_forms": feedback_forms(db, student),
        "placement": placement(db, student, res, attendance),
        "remarks": remarks(db, student.id, include_private=True),
        "help_requests": help_requests(db, student.id),
    }
