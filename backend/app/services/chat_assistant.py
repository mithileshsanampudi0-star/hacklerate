"""Campus analytics chat assistant grounded in database records with strict RBAC."""

import re
from typing import Any
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.academic import Course, CourseResult, SemesterResult
from app.models.activity import Assignment, AssignmentSubmission
from app.models.analytics import (
    AcademicRiskPrediction,
    Intervention,
    PlacementReadinessScore,
    StudentSegment,
    StudentSuccessScore,
)
from app.models.identity import Department, Faculty, Student, User
from app.services import student_data as sd
from app.services.academic_risk import predict_academic_risk
from app.services.placement_readiness import calculate_placement_readiness
from app.services.placement_risk import predict_placement_risk
from app.services.success_score import calculate_student_success_score


def process_chat_query(db: Session, user: User, message: str) -> dict[str, Any]:
    """Processes a natural language query with verified database grounding and RBAC enforcement."""
    query = message.strip().lower()
    role = user.role.value

    # Identify user context
    student_ctx = None
    faculty_ctx = None
    if role == "student":
        student_ctx = db.scalar(select(Student).where(Student.user_id == user.id))
    elif role == "faculty":
        faculty_ctx = db.scalar(select(Faculty).where(Faculty.user_id == user.id))

    # --- Student Role Questions ---
    if role == "student":
        if not student_ctx:
            return {"answer": "Student profile not found.", "sources": []}

        if any(w in query for w in ["success score", "score breakdown", "why is my score"]):
            ss = calculate_student_success_score(db, student_ctx, save_snapshot=False)
            breakdown_lines = [
                f"- **{v['label']}**: {v['raw']} (Normalized: {v['normalized']}/100, Contributed: {v['contribution']} pts)"
                for v in ss["breakdown"].values()
            ]
            return {
                "answer": (
                    f"Your overall **Student Success Score is {ss['overall_score']}/100** (Category: **{ss['score_category']}**).\n\n"
                    f"### Indicator Breakdown:\n" + "\n".join(breakdown_lines) + "\n\n"
                    f"> *Observed metrics: CGPA, attendance, and assignment completion are computed from live course logs.*"
                ),
                "sources": ["StudentSuccessScoreEngine", "EnrollmentRecords", "LMSActivity"],
            }

        if any(w in query for w in ["attendance", "classes needed", "shortage"]):
            att = sd.attendance_report(db, student_ctx)
            ov = att["overall"]
            pct = ov["percentage"]
            if pct and pct < 75.0:
                needed = ov.get("classes_needed", 0)
                return {
                    "answer": (
                        f"Your current attendance is **{pct:.1f}%**, which is below the institutional 75% requirement.\n\n"
                        f"You need to attend **{needed} consecutive classes** without absence to restore your attendance to 75%.\n"
                        f"Courses with attendance risks: **{att['courses_at_risk']}**."
                    ),
                    "sources": ["AttendanceRecords", "Services.Attendance"],
                }
            return {
                "answer": f"Your current attendance is **{pct:.1f}%** ({ov['attended']}/{ov['total']} classes attended). You are in the **Safe** category.",
                "sources": ["AttendanceRecords"],
            }

        if any(w in query for w in ["placement", "readiness", "interview", "coding"]):
            pr = calculate_placement_readiness(db, student_ctx, save_snapshot=False)
            strengths = "\n".join([f"- {s}" for s in pr["strengths"]]) or "- Balanced baseline"
            gaps = "\n".join([f"- {g}" for g in pr["skill_gaps"]]) or "- No major skill gaps flagged"
            recs = "\n".join([f"- {r}" for r in pr["recommendations"]])
            return {
                "answer": (
                    f"Your **Placement Readiness Score is {pr['overall_score']}/100** ({pr['category']}).\n\n"
                    f"**Identified Strengths:**\n{strengths}\n\n"
                    f"**Skill Gaps to Address:**\n{gaps}\n\n"
                    f"**Personalized Recommendations:**\n{recs}"
                ),
                "sources": ["PlacementReadinessEngine", "SkillAssessment"],
            }

        if any(w in query for w in ["risk", "academic risk", "falling behind"]):
            risk = predict_academic_risk(db, student_ctx, save_prediction=False)
            factors = "\n".join([f"- **{f['factor']}**: {f['detail']}" for f in risk["contributing_factors"]])
            actions = "\n".join([f"- {a}" for a in risk["suggested_interventions"]])
            return {
                "answer": (
                    f"Your predicted **Academic Risk is {risk['risk_probability']}%** (Category: **{risk['risk_category'].upper()}**).\n\n"
                    f"### Key Contributing Factors:\n{factors}\n\n"
                    f"### Recommended Actions:\n{actions}\n\n"
                    f"> *Model version: {risk['model_version']}. Generated using validated course performance indicators.*"
                ),
                "sources": ["AcademicRiskMLPipeline"],
            }

        if any(w in query for w in ["assignment", "homework", "due"]):
            assigns = sd.assignments(db, student_ctx)
            items = [a for a in assigns["items"] if a["status"] in ("pending", "overdue")]
            if items:
                lines = [f"- **{a['course_code']}**: {a['title']} (Due: {a['due_date']}, Status: {a['status'].upper()})" for a in items]
                return {
                    "answer": f"You have **{len(items)} pending/overdue assignment(s)**:\n\n" + "\n".join(lines),
                    "sources": ["AssignmentSubmissions"],
                }
            return {
                "answer": "Great job! You have no pending or overdue assignments at this time.",
                "sources": ["AssignmentSubmissions"],
            }

        # Default student guidance
        return {
            "answer": (
                f"Hello {student_ctx.name}! As a student, you can ask me about:\n"
                f"- **My Student Success Score** and indicator breakdown\n"
                f"- **My Attendance** and classes needed to reach 75%\n"
                f"- **My Placement Readiness** and personalized recommendations\n"
                f"- **My Academic Risk** and actionable intervention steps\n"
                f"- **My Upcoming Assignments** and deadlines"
            ),
            "sources": ["CampusAssistant"],
        }

    # --- Faculty & Admin Role Queries ---
    dept_id = faculty_ctx.department_id if faculty_ctx else None

    # Check for specific student inquiries: e.g. "student 24cse007", "Aarav", or roll number
    roll_match = re.search(r"\b(24cse\d{3})\b", query)
    if roll_match:
        roll = roll_match.group(1)
        target = db.scalar(select(Student).where(func.lower(Student.roll_no) == roll.lower()))
        if target:
            if faculty_ctx and target.department_id != faculty_ctx.department_id:
                return {
                    "answer": f"Student {roll} belongs to another department. You only have access to your department's records.",
                    "sources": ["RBACPolicy"],
                }
            risk = predict_academic_risk(db, target, save_prediction=False)
            pr = calculate_placement_readiness(db, target, save_snapshot=False)
            ss = calculate_student_success_score(db, target, save_snapshot=False)
            factors = "\n".join([f"- {f['factor']}: {f['detail']}" for f in risk["contributing_factors"]])
            return {
                "answer": (
                    f"### Student Profile: {target.name} ({target.roll_no})\n"
                    f"- **Section:** {target.section} | **Semester:** {target.current_semester}\n"
                    f"- **Student Success Score:** {ss['overall_score']}/100 ({ss['score_category']})\n"
                    f"- **Academic Risk:** {risk['risk_probability']}% (**{risk['risk_category'].upper()}**)\n"
                    f"- **Placement Readiness:** {pr['overall_score']}/100 ({pr['category']})\n\n"
                    f"**Contributing Risk Factors:**\n{factors}"
                ),
                "sources": ["StudentProfile", "AcademicRiskPrediction", "PlacementReadinessScore"],
            }

    # "Which students need immediate intervention?" or "high risk students"
    if any(w in query for w in ["immediate intervention", "high risk", "at risk", "at-risk", "need help"]):
        stmt = select(Student)
        if dept_id:
            stmt = stmt.where(Student.department_id == dept_id)
        students = db.scalars(stmt).all()

        high_risk_list = []
        for s in students:
            r = predict_academic_risk(db, s, save_prediction=False)
            if r["risk_category"] == "high":
                high_risk_list.append((s, r["risk_probability"], r["contributing_factors"]))

        if high_risk_list:
            high_risk_list.sort(key=lambda x: x[1], reverse=True)
            lines = [
                f"- **{s.name}** ({s.roll_no}, Sec {s.section}): Risk **{prob}%** — *{factors[0]['factor'] if factors else 'Multiple factors'}*"
                for s, prob, factors in high_risk_list[:8]
            ]
            return {
                "answer": (
                    f"Found **{len(high_risk_list)} student(s) classified as High Academic Risk**:\n\n"
                    + "\n".join(lines)
                    + "\n\n> *Navigate to Faculty Interventions to review and assign remediation plans.*"
                ),
                "sources": ["AcademicRiskPredictor", "StudentRecords"],
            }
        return {
            "answer": "No students are currently classified under high academic risk in your jurisdiction.",
            "sources": ["AcademicRiskPredictor"],
        }

    # "Which department has highest CGPA" or department comparisons
    if any(w in query for w in ["department", "highest cgpa", "compare", "departments"]):
        depts = db.scalars(select(Department)).all()
        dept_data = []
        for d in depts:
            cgpas = [
                r.cgpa_upto
                for r in db.execute(
                    select(SemesterResult.cgpa_upto)
                    .join(Student, Student.id == SemesterResult.student_id)
                    .where(Student.department_id == d.id, SemesterResult.cgpa_upto.isnot(None))
                )
            ]

            avg = round(sum(cgpas) / len(cgpas), 2) if cgpas else 0.0
            dept_data.append((d.name, d.code, avg, len(cgpas)))

        dept_data.sort(key=lambda x: x[2], reverse=True)
        lines = [f"- **{name} ({code})**: Average CGPA **{avg:.2f}** ({count} student records)" for name, code, avg, count in dept_data]
        top = dept_data[0]
        return {
            "answer": (
                f"### Department CGPA Benchmarks:\n"
                f"The department with the highest average CGPA is **{top[0]} ({top[1]})** with an average of **{top[2]:.2f}**.\n\n"
                + "\n".join(lines)
            ),
            "sources": ["SemesterResults", "DepartmentAggregations"],
        }

    # "Which students have low placement readiness?"
    if any(w in query for w in ["low placement", "placement readiness", "placement weak", "need placement"]):
        stmt = select(Student)
        if dept_id:
            stmt = stmt.where(Student.department_id == dept_id)
        students = db.scalars(stmt).all()

        low_pr = []
        for s in students:
            pr = calculate_placement_readiness(db, s, save_snapshot=False)
            if pr["overall_score"] < 60.0:
                low_pr.append((s, pr["overall_score"], pr["skill_gaps"]))

        low_pr.sort(key=lambda x: x[1])
        if low_pr:
            lines = [
                f"- **{s.name}** ({s.roll_no}): Readiness **{score:.1f}/100** ({gaps[0] if gaps else 'Skill gaps'})"
                for s, score, gaps in low_pr[:8]
            ]
            return {
                "answer": (
                    f"**{len(low_pr)} student(s)** have placement readiness below 60/100:\n\n"
                    + "\n".join(lines)
                ),
                "sources": ["PlacementReadinessEngine"],
            }
        return {
            "answer": "All evaluated students currently exceed the 60/100 placement readiness baseline.",
            "sources": ["PlacementReadinessEngine"],
        }

    # "Pending interventions"
    if any(w in query for w in ["pending interventions", "active interventions", "action items"]):
        stmt = select(Intervention).where(Intervention.status.in_(["pending", "in_progress"]))
        if dept_id:
            stmt = stmt.join(Student, Student.id == Intervention.student_id).where(Student.department_id == dept_id)
        pending = db.scalars(stmt).all()
        if pending:
            lines = [
                f"- **{i.title}** for {i.student.name if i.student else 'Student'} (Status: {i.status.upper()}, Urgency: {i.urgency.upper()})"
                for i in pending[:6]
            ]
            return {
                "answer": f"There are **{len(pending)} active/pending intervention(s)**:\n\n" + "\n".join(lines),
                "sources": ["InterventionsDatabase"],
            }
        return {
            "answer": "There are currently no unresolved pending interventions.",
            "sources": ["InterventionsDatabase"],
        }

    # "Incomplete assignments"
    if any(w in query for w in ["incomplete assignments", "missing assignments", "unsubmitted"]):
        stmt = select(Student)
        if dept_id:
            stmt = stmt.where(Student.department_id == dept_id)
        students = db.scalars(stmt).all()

        missing_list = []
        for s in students:
            assigns = sd.assignments(db, s)
            overdue = assigns.get("pending", 0) + assigns.get("overdue", 0)
            if overdue > 0:
                missing_list.append((s, overdue))

        missing_list.sort(key=lambda x: x[1], reverse=True)
        if missing_list:
            lines = [f"- **{s.name}** ({s.roll_no}, Sec {s.section}): **{cnt} missing/overdue** assignment(s)" for s, cnt in missing_list[:8]]
            return {
                "answer": f"**{len(missing_list)} student(s)** have pending or overdue assignments:\n\n" + "\n".join(lines),
                "sources": ["AssignmentSubmissions"],
            }
        return {
            "answer": "All enrolled students have completed their coursework assignments.",
            "sources": ["AssignmentSubmissions"],
        }

    # Default guidance for faculty/admin
    return {
        "answer": (
            f"Hello {user.email}! I am your Campus Analytics Assistant. You can ask queries such as:\n"
            f"- **'Which students need immediate intervention?'**\n"
            f"- **'Why is student 24cse007 classified as high academic risk?'**\n"
            f"- **'Which department has the highest average CGPA?'**\n"
            f"- **'Which students have low placement readiness?'**\n"
            f"- **'Which students have incomplete assignments?'**\n"
            f"- **'What interventions are pending?'**"
        ),
        "sources": ["CampusAnalyticsQAPipeline"],
    }
