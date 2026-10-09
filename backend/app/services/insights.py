"""Smart Insights Generator: computes deterministic, verified insights from live data."""

from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.academic import CourseResult, SemesterResult
from app.models.activity import Assignment, AssignmentSubmission
from app.models.analytics import Intervention, LMSActivity
from app.models.identity import Department, Faculty, Student
from app.services import student_data as sd
from app.services.academic_risk import predict_academic_risk
from app.services.placement_readiness import calculate_placement_readiness


def generate_campus_insights(
    db: Session,
    department_id: int | None = None,
    faculty_id: int | None = None,
) -> list[dict[str, Any]]:
    """Generates deterministic, verified actionable campus insights."""
    insights = []

    stmt = select(Student)
    if department_id:
        stmt = stmt.where(Student.department_id == department_id)
    students = db.scalars(stmt).all()
    if not students:
        return []

    # 1. Attendance Crisis Insight
    critical_att = []
    warning_att = []
    for s in students:
        att = sd.attendance_report(db, s)
        pct = att.get("overall", {}).get("percentage")
        if pct is not None:
            if pct < 75.0:
                critical_att.append((s, pct))
            elif pct < 80.0:
                warning_att.append((s, pct))

    if critical_att:
        insights.append({
            "id": "insight_att_critical",
            "type": "attendance",
            "severity": "critical",
            "title": f"{len(critical_att)} Student(s) Below 75% Attendance Threshold",
            "summary": f"{len(critical_att)} students have attendance under 75% and risk semester exam detentions.",
            "impact": "Students face mandatory condonation fines or semester debarment unless attendance recovers.",
            "recommendation": "Review attendance recovery plans and schedule immediate counseling.",
            "action_link": "/faculty/students?risk=critical",
            "stat": f"{len(critical_att)} students",
        })

    # 2. Placement Readiness Benchmark Insight
    ready_placement = []
    need_placement_support = []
    for s in students:
        readiness = calculate_placement_readiness(db, s, save_snapshot=False)
        score = readiness["overall_score"]
        if score >= 75.0:
            ready_placement.append(s)
        elif score < 60.0:
            need_placement_support.append(s)

    if ready_placement:
        pct_ready = round(len(ready_placement) / len(students) * 100.0, 1)
        insights.append({
            "id": "insight_placement_ready",
            "type": "placement",
            "severity": "success",
            "title": f"{len(ready_placement)} Students ({pct_ready}%) are Placement Ready",
            "summary": f"{len(ready_placement)} candidate(s) meet or exceed the 75/100 readiness benchmark across coding, aptitude, and interviews.",
            "impact": "Eligible for tier-1 company early campus recruitment drives and priority interviews.",
            "recommendation": "Coordinate with training and placement cell to share profiles with recruiting partners.",
            "action_link": "/admin/placement" if not faculty_id else "/faculty/students",
            "stat": f"{pct_ready}% ready",
        })

    if len(need_placement_support) > len(students) * 0.3:
        insights.append({
            "id": "insight_placement_gap",
            "type": "placement",
            "severity": "warning",
            "title": f"{len(need_placement_support)} Students Require Placement Acceleration",
            "summary": "Over 30% of students exhibit skill gaps in competitive coding assessments or mock interviews.",
            "impact": "Campus placement conversion rate could decrease in the upcoming recruitment cycle.",
            "recommendation": "Conduct department-level algorithm bootcamps and quantitative aptitude sprints.",
            "action_link": "/faculty/interventions",
            "stat": f"{len(need_placement_support)} students",
        })

    # 3. High Academic Risk Without Active Interventions
    high_risk_unmanaged = []
    for s in students:
        risk = predict_academic_risk(db, s, save_prediction=False)
        if risk["risk_category"] == "high":
            # Check if active intervention exists
            active_it = db.scalar(
                select(Intervention.id)
                .where(
                    Intervention.student_id == s.id,
                    Intervention.status.in_(["pending", "in_progress"]),
                )
                .limit(1)
            )
            if not active_it:
                high_risk_unmanaged.append(s)

    if high_risk_unmanaged:
        insights.append({
            "id": "insight_unmanaged_risk",
            "type": "intervention",
            "severity": "critical",
            "title": f"{len(high_risk_unmanaged)} High-Risk Student(s) Lack Active Intervention",
            "summary": f"{len(high_risk_unmanaged)} student(s) classified with high academic risk do not have an active intervention plan registered.",
            "impact": "Without proactive intervention, risk of academic failure or course repetition is elevated.",
            "recommendation": "Assign faculty mentors and define personalized remediation action steps immediately.",
            "action_link": "/faculty/interventions",
            "stat": f"{len(high_risk_unmanaged)} unassigned",
        })

    # 4. Department Academic Performance Benchmark
    all_cgpas = [
        r.cgpa_upto
        for r in db.execute(
            select(SemesterResult.cgpa_upto).where(SemesterResult.cgpa_upto.isnot(None))
        )
    ]
    if all_cgpas:
        campus_avg_cgpa = sum(all_cgpas) / len(all_cgpas)
        dept_cgpas = [
            r.cgpa_upto
            for r in db.execute(
                select(SemesterResult.cgpa_upto)
                .join(Student, Student.id == SemesterResult.student_id)
                .where(
                    SemesterResult.cgpa_upto.isnot(None),
                    Student.department_id == (department_id or (students[0].department_id if students else 1)),
                )
            )
        ]

        if dept_cgpas:
            dept_avg = sum(dept_cgpas) / len(dept_cgpas)
            diff = dept_avg - campus_avg_cgpa
            if diff >= 0.2:
                insights.append({
                    "id": "insight_cgpa_outperform",
                    "type": "academic",
                    "severity": "success",
                    "title": f"Department CGPA ({dept_avg:.2f}) Exceeds Campus Benchmark ({campus_avg_cgpa:.2f})",
                    "summary": f"Average CGPA is +{diff:.2f} points higher than the overall institutional average.",
                    "impact": "Reflects strong faculty instructional delivery and high student examination performance.",
                    "recommendation": "Document high-performing teaching methodologies for peer department review.",
                    "action_link": "/faculty/students",
                    "stat": f"+{diff:.2f} CGPA",
                })
            elif diff <= -0.2:
                insights.append({
                    "id": "insight_cgpa_lag",
                    "type": "academic",
                    "severity": "warning",
                    "title": f"Department CGPA ({dept_avg:.2f}) Trails Campus Average ({campus_avg_cgpa:.2f})",
                    "summary": f"Cumulative GPA is {abs(diff):.2f} points lower than the campus-wide benchmark.",
                    "impact": "May affect accreditation metrics and placement shortlisting.",
                    "recommendation": "Organize mid-semester revision workshops for conceptually challenging subjects.",
                    "action_link": "/faculty/students",
                    "stat": f"-{abs(diff):.2f} CGPA",
                })

    return insights
