"""Intervention Recommendation and Tracking Engine."""

from datetime import date, datetime
import math
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.analytics import Intervention
from app.models.identity import Faculty, Student
from app.services import student_data as sd
from app.services.academic_risk import predict_academic_risk
from app.services.placement_risk import predict_placement_risk


def generate_recommended_interventions(db: Session, student: Student) -> list[dict[str, Any]]:
    """Generates personalized, prioritized recommendations based on real metrics."""
    recommendations = []

    # 1. Attendance checks
    att = sd.attendance_report(db, student)
    overall = att.get("overall", {})
    att_pct = float(overall.get("percentage") or 75.0)
    attended = int(overall.get("attended") or 0)
    total = int(overall.get("total") or 0)

    if att_pct < 75.0:
        needed = max(1, math.ceil((75 * total - 100 * attended) / 25))
        recommendations.append({
            "category": "attendance",
            "title": f"Mandatory Attendance Recovery Plan ({needed} classes needed)",
            "urgency": "critical" if att_pct < 70.0 else "high",
            "reason": f"Current attendance of {att_pct:.1f}% is below the mandatory 75% institutional requirement.",
            "description": f"To reach 75%, you need to attend the next {needed} consecutive class periods without any unauthorized absence.",
            "action_steps": [
                f"Attend at least {needed} consecutive class sessions without absence.",
                "Meet designated faculty mentor to register your attendance improvement plan.",
                "Submit medical certificates or approved OD letters for past missed dates if applicable.",
            ],
        })

    # 2. Assignment checks
    assigns = sd.assignments(db, student)
    overdue_items = [a for a in assigns.get("items", []) if a.get("status") in ("overdue", "pending")]
    if overdue_items:
        overdue_titles = [f"{a['course_code']}: {a['title']}" for a in overdue_items[:3]]
        recommendations.append({
            "category": "academic",
            "title": f"Submission of {len(overdue_items)} Incomplete Course Assignment(s)",
            "urgency": "high" if len(overdue_items) >= 2 else "medium",
            "reason": f"{len(overdue_items)} assignment(s) are pending or overdue in current courses.",
            "description": f"Outstanding deliverables: {', '.join(overdue_titles)}",
            "action_steps": [
                f"Complete {a['title']} ({a['course_code']}) by the extended submission date." for a in overdue_items[:3]
            ] + ["Request assignment doubts clearance during faculty office hours."],
        })

    # 3. Academic Risk checks
    acad_risk = predict_academic_risk(db, student, save_prediction=False)
    if acad_risk["risk_category"] == "high":
        recommendations.append({
            "category": "academic",
            "title": "Academic Remedial Mentoring Program",
            "urgency": "high",
            "reason": f"Academic risk predicted at {acad_risk['risk_probability']}%. Key drivers: {', '.join([f['factor'] for f in acad_risk['contributing_factors'][:2]])}",
            "description": "Comprehensive academic support plan with specialized peer tutoring and concept revision.",
            "action_steps": acad_risk["suggested_interventions"][:3],
        })

    # 4. Placement Risk checks
    place_risk = predict_placement_risk(db, student, save_prediction=False)
    if place_risk["risk_category"] in ("high", "medium"):
        recommendations.append({
            "category": "placement",
            "title": "Technical Placement Readiness Acceleration",
            "urgency": "high" if place_risk["risk_category"] == "high" else "medium",
            "reason": f"Placement readiness score is {place_risk['readiness_score']:.1f}/100 with identified skill gaps.",
            "description": "Tailored training in coding assessments, quantitative aptitude, and technical interviews.",
            "action_steps": place_risk["recommendations"][:3],
        })

    # If no critical risks, suggest advancement
    if not recommendations:
        recommendations.append({
            "category": "placement",
            "title": "Advanced Competitive Edge & Hackathon Participation",
            "urgency": "low",
            "reason": "Strong performance across academics and attendance.",
            "description": "Participate in national coding competitions, open-source contributions, or cloud certifications.",
            "action_steps": [
                "Register for upcoming inter-college hackathons or algorithmic contests.",
                "Prepare for top-tier product company campus placement tracks.",
            ],
        })

    return recommendations


def list_interventions_for_student(db: Session, student_id: int) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(Intervention)
        .where(Intervention.student_id == student_id)
        .order_by(Intervention.created_at.desc())
    ).all()
    return [_serialize_intervention(r) for r in rows]


def list_interventions_for_faculty(
    db: Session,
    faculty_id: int | None = None,
    department_id: int | None = None,
    status_filter: str | None = None,
) -> list[dict[str, Any]]:
    stmt = select(Intervention).join(Student, Student.id == Intervention.student_id)
    if department_id:
        stmt = stmt.where(Student.department_id == department_id)
    if faculty_id:
        stmt = stmt.where(Intervention.faculty_id == faculty_id)
    if status_filter:
        stmt = stmt.where(Intervention.status == status_filter)

    rows = db.scalars(stmt.order_by(Intervention.created_at.desc())).all()
    return [_serialize_intervention(r) for r in rows]


def create_intervention(
    db: Session,
    student_id: int,
    faculty_id: int | None,
    category: str,
    title: str,
    description: str,
    urgency: str = "medium",
    action_steps: list[str] | None = None,
    target_date: date | None = None,
) -> Intervention:
    it = Intervention(
        student_id=student_id,
        faculty_id=faculty_id,
        category=category,
        title=title,
        description=description,
        urgency=urgency,
        action_steps=action_steps or [],
        target_date=target_date,
        status="pending",
    )
    db.add(it)
    db.commit()
    db.refresh(it)
    return it


def update_intervention_status(
    db: Session,
    intervention_id: int,
    status: str,
    notes: str | None = None,
    outcome: str | None = None,
    is_faculty: bool = False,
) -> Intervention:
    it = db.get(Intervention, intervention_id)
    if not it:
        raise ValueError("Intervention not found")

    it.status = status
    if is_faculty:
        if notes:
            it.faculty_notes = notes
        if outcome:
            it.outcome = outcome
    else:
        if notes:
            it.student_notes = notes

    if status in ("completed", "dismissed"):
        it.completed_at = datetime.now()

    db.commit()
    db.refresh(it)
    return it


def _serialize_intervention(it: Intervention) -> dict[str, Any]:
    return {
        "id": it.id,
        "student_id": it.student_id,
        "student_name": it.student.name if it.student else None,
        "student_roll": it.student.roll_no if it.student else None,
        "faculty_id": it.faculty_id,
        "faculty_name": it.faculty.name if it.faculty else None,
        "category": it.category,
        "title": it.title,
        "description": it.description,
        "urgency": it.urgency,
        "status": it.status,
        "action_steps": it.action_steps or [],
        "student_notes": it.student_notes,
        "faculty_notes": it.faculty_notes,
        "outcome": it.outcome,
        "target_date": it.target_date.isoformat() if it.target_date else None,
        "created_at": it.created_at.isoformat() if it.created_at else None,
        "completed_at": it.completed_at.isoformat() if it.completed_at else None,
    }
