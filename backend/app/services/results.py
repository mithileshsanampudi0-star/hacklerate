"""Turn exam marks into course grades and refresh the cached semester_results table."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Course, CourseResult, Enrollment, Exam, ExamMark, Semester, SemesterResult
from app.services import gpa


def course_total(exam_rows: list[tuple[float, float, float | None]]) -> float:
    """exam_rows: (max_marks, weightage, marks_obtained). Missing marks count as 0."""
    return round(sum((m or 0) / mx * w for mx, w, m in exam_rows if mx), 2)


def publish_course_results(db: Session, course_id: int, semester_id: int) -> int:
    """Compute grades for every enrollment of a course offering. Returns rows written."""
    enrollments = db.scalars(
        select(Enrollment).where(Enrollment.course_id == course_id, Enrollment.semester_id == semester_id)
    ).all()
    exams = db.scalars(select(Exam).where(Exam.course_id == course_id, Exam.semester_id == semester_id)).all()
    marks = {
        (m.exam_id, m.student_id): m.marks_obtained
        for m in db.scalars(select(ExamMark).where(ExamMark.exam_id.in_([e.id for e in exams])))
    }
    existing = {
        r.enrollment_id: r
        for r in db.scalars(
            select(CourseResult).where(CourseResult.enrollment_id.in_([e.id for e in enrollments]))
        )
    }

    for enr in enrollments:
        total = course_total([(e.max_marks, e.weightage, marks.get((e.id, enr.student_id))) for e in exams])
        grade, points = gpa.grade_for_total(total)
        row = existing.get(enr.id) or CourseResult(enrollment_id=enr.id)
        row.total_marks, row.grade, row.grade_points = total, grade, points
        db.add(row)
    db.flush()

    for student_id in {e.student_id for e in enrollments}:
        refresh_semester_results(db, student_id)
    return len(enrollments)


def refresh_semester_results(db: Session, student_id: int) -> None:
    rows = db.execute(
        select(Semester.id, Semester.number, Course.id, Course.credits, CourseResult.grade_points)
        .select_from(CourseResult)
        .join(Enrollment, Enrollment.id == CourseResult.enrollment_id)
        .join(Course, Course.id == Enrollment.course_id)
        .join(Semester, Semester.id == Enrollment.semester_id)
        .where(Enrollment.student_id == student_id)
    ).all()
    sem_ids = {number: sid for sid, number, *_ in rows}
    summary = gpa.summarize(gpa.CourseGrade(number, cid, credits, gp) for _, number, cid, credits, gp in rows)

    db.execute(delete(SemesterResult).where(SemesterResult.student_id == student_id))
    for s in summary["semesters"]:
        db.add(
            SemesterResult(
                student_id=student_id,
                semester_id=sem_ids[s["semester"]],
                sgpa=s["sgpa"],
                credits_earned=s["credits_earned"],
                cgpa_upto=s["cgpa_upto"],
            )
        )
    db.flush()


def latest_cgpa(db: Session, student_id: int) -> float | None:
    return db.scalar(
        select(SemesterResult.cgpa_upto)
        .join(Semester, Semester.id == SemesterResult.semester_id)
        .where(SemesterResult.student_id == student_id)
        .order_by(Semester.number.desc())
        .limit(1)
    )
