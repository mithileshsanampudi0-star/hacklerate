"""Student Success Score Engine: 0 to 100 comprehensive composite score."""

from datetime import datetime
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.academic import SemesterResult
from app.models.activity import Activity, AssignmentSubmission, Certification, SubmissionStatus
from app.models.analytics import LMSActivity, PlacementReadinessScore, StudentSuccessScore
from app.models.engagement import FeedbackResponse
from app.models.identity import Student
from app.services import student_data as sd
from app.services.placement_readiness import calculate_placement_readiness
from app.services.settings import get_success_score_weights


def calculate_student_success_score(
    db: Session,
    student: Student,
    save_snapshot: bool = True,
) -> dict[str, Any]:
    weights = get_success_score_weights(db)

    # 1. CGPA Component (30%)
    res = sd.results(db, student.id)
    cgpa = res.get("cgpa")
    cgpa_norm = min(100.0, max(0.0, (cgpa / 10.0) * 100.0)) if cgpa is not None else None

    # 2. Attendance Component (20%)
    att_report = sd.attendance_report(db, student)
    att_pct = att_report.get("overall", {}).get("percentage")
    att_norm = min(100.0, max(0.0, float(att_pct))) if att_pct is not None else None

    # 3. LMS Activity Component (15%)
    lms = db.scalar(select(LMSActivity).where(LMSActivity.student_id == student.id))
    if lms:
        # benchmark: 30 logins, 25 course views, 20 videos, 10 assignments
        lms_points = (
            min(1.0, lms.login_count / 30.0) * 30.0
            + min(1.0, lms.course_views / 25.0) * 30.0
            + min(1.0, lms.videos_watched / 20.0) * 25.0
            + min(1.0, lms.time_spent_hours / 40.0) * 15.0
        )
        lms_norm = round(min(100.0, max(0.0, lms_points)), 1)
    else:
        lms_norm = 70.0  # reasonable neutral default when LMS is not yet activated

    # 4. Assignment Completion Component (10%)
    assign_data = sd.assignments(db, student)
    items = assign_data.get("items", [])
    if items:
        completed = sum(1 for a in items if a.get("status") in ("submitted", "graded"))
        assign_norm = round((completed / len(items)) * 100.0, 1)
    else:
        assign_norm = 100.0

    # 5. Certifications Component (10%)
    certs = sd.certifications(db, student.id)
    if certs:
        verified_count = sum(1 for c in certs if c.get("verified"))
        unverified_count = len(certs) - verified_count
        cert_norm = min(100.0, verified_count * 40.0 + unverified_count * 20.0)
    else:
        cert_norm = 40.0  # basic starting floor

    # 6. Placement Progress Component (10%)
    last_pr = db.scalar(
        select(PlacementReadinessScore)
        .where(PlacementReadinessScore.student_id == student.id)
        .order_by(PlacementReadinessScore.calculated_at.desc())
        .limit(1)
    )
    if last_pr:
        placement_norm = last_pr.overall_score
    else:
        pr_calc = calculate_placement_readiness(db, student, save_snapshot=False)
        placement_norm = pr_calc["overall_score"]

    # 7. Feedback & Engagement (5%)
    feedback_count = db.scalar(
        select(func.count(FeedbackResponse.id)).where(FeedbackResponse.student_id == student.id)
    ) or 0
    activity_count = db.scalar(
        select(func.count(Activity.id)).where(Activity.student_id == student.id)
    ) or 0
    engagement_norm = min(100.0, (feedback_count * 20.0) + (activity_count * 25.0))
    if engagement_norm < 50.0:
        engagement_norm = max(engagement_norm, 50.0)

    # Dictionary of components
    components = {
        "cgpa": {
            "label": "CGPA Academic Record",
            "raw": f"{cgpa:.2f}" if cgpa is not None else "N/A",
            "normalized": cgpa_norm if cgpa_norm is not None else 70.0,
            "weight": weights.get("cgpa", 0.30),
        },
        "attendance": {
            "label": "Class Attendance",
            "raw": f"{att_pct:.1f}%" if att_pct is not None else "N/A",
            "normalized": att_norm if att_norm is not None else 75.0,
            "weight": weights.get("attendance", 0.20),
        },
        "lms": {
            "label": "LMS Learning Activity",
            "raw": f"{lms.login_count} logins, {lms.videos_watched} vids" if lms else "Default",
            "normalized": lms_norm,
            "weight": weights.get("lms", 0.15),
        },
        "assignments": {
            "label": "Assignment Completion",
            "raw": f"{assign_norm:.0f}% submitted",
            "normalized": assign_norm,
            "weight": weights.get("assignments", 0.10),
        },
        "certifications": {
            "label": "Industry Certifications",
            "raw": f"{len(certs)} certifications",
            "normalized": cert_norm,
            "weight": weights.get("certifications", 0.10),
        },
        "placement": {
            "label": "Placement Readiness Progress",
            "raw": f"{placement_norm:.1f}/100 readiness",
            "normalized": placement_norm,
            "weight": weights.get("placement", 0.10),
        },
        "feedback": {
            "label": "Engagement & Feedback",
            "raw": f"{feedback_count} feedback, {activity_count} activities",
            "normalized": engagement_norm,
            "weight": weights.get("feedback", 0.05),
        },
    }

    # Fair missing data handling: sum weights of present components
    total_active_weight = sum(c["weight"] for c in components.values()) or 1.0
    overall = sum((c["normalized"] * c["weight"]) for c in components.values()) / total_active_weight
    overall = round(min(100.0, max(0.0, overall)), 1)

    # Category
    if overall >= 85.0:
        score_category = "Excellent"
    elif overall >= 70.0:
        score_category = "Good"
    elif overall >= 55.0:
        score_category = "Average"
    else:
        score_category = "At Risk"

    # Component breakdown with contribution
    breakdown = {}
    for k, v in components.items():
        contrib = round((v["normalized"] * v["weight"]) / total_active_weight, 2)
        breakdown[k] = {
            "label": v["label"],
            "raw": v["raw"],
            "normalized": v["normalized"],
            "weight": v["weight"],
            "contribution": contrib,
            "impact": "positive" if v["normalized"] >= 75.0 else ("warning" if v["normalized"] >= 60.0 else "negative"),
        }

    # Historical trend for this student
    history_rows = db.scalars(
        select(StudentSuccessScore)
        .where(StudentSuccessScore.student_id == student.id)
        .order_by(StudentSuccessScore.calculated_at.desc())
        .limit(6)
    ).all()
    history = [
        {
            "score": h.overall_score,
            "category": h.score_category,
            "date": h.calculated_at.strftime("%d %b"),
        }
        for h in reversed(history_rows)
    ]

    result = {
        "overall_score": overall,
        "score_category": score_category,
        "breakdown": breakdown,
        "history": history,
        "calculated_at": datetime.now(),
    }

    if save_snapshot:
        snapshot = StudentSuccessScore(
            student_id=student.id,
            overall_score=overall,
            score_category=score_category,
            cgpa_component=components["cgpa"]["normalized"],
            attendance_component=components["attendance"]["normalized"],
            lms_component=components["lms"]["normalized"],
            assignment_component=components["assignments"]["normalized"],
            certification_component=components["certifications"]["normalized"],
            placement_component=components["placement"]["normalized"],
            feedback_component=components["feedback"]["normalized"],
            breakdown=breakdown,
        )
        db.add(snapshot)
        db.commit()

    return result
