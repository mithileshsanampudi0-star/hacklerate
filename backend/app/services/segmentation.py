"""Student Segmentation Engine: automatically segments students with clear rationale."""

from datetime import datetime
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analytics import (
    AcademicRiskPrediction,
    PlacementReadinessScore,
    StudentSegment,
    StudentSuccessScore,
)
from app.models.identity import Student
from app.services import student_data as sd
from app.services.placement_readiness import calculate_placement_readiness
from app.services.success_score import calculate_student_success_score

SEGMENTS = {
    "A": {
        "code": "A",
        "name": "Top Performers",
        "description": "Exemplary CGPA, consistent attendance, excellent assignment completion, and high success score.",
        "color": "emerald",
    },
    "B": {
        "code": "B",
        "name": "Academically Strong, Placement Weak",
        "description": "Solid academic standing (CGPA >= 7.0) but requires targeted placement and technical skill interventions.",
        "color": "amber",
    },
    "C": {
        "code": "C",
        "name": "Placement Ready",
        "description": "High coding, aptitude, and interview scores ready for top placement drives.",
        "color": "indigo",
    },
    "D": {
        "code": "D",
        "name": "Needs Immediate Intervention",
        "description": "Critical attendance, active backlogs, or elevated academic risk requiring urgent remediation.",
        "color": "rose",
    },
}


def classify_student_segment(
    db: Session,
    student: Student,
    save_record: bool = True,
) -> dict[str, Any]:
    """Classifies a student into a primary segment based on verified metrics and provides reasons."""
    res = sd.results(db, student.id)
    cgpa = res.get("cgpa") or 6.5
    backlogs = res.get("active_backlogs", 0)

    att = sd.attendance_report(db, student)
    att_pct = float(att.get("overall", {}).get("percentage") or 75.0)

    assigns = sd.assignments(db, student)
    total_assigns = len(assigns.get("items", []))
    missing_assigns = assigns.get("pending", 0) + assigns.get("overdue", 0)
    assign_comp_pct = (
        ((total_assigns - missing_assigns) / total_assigns * 100.0)
        if total_assigns > 0
        else 80.0
    )

    # Success score
    success = calculate_student_success_score(db, student, save_snapshot=False)
    success_score = success["overall_score"]

    # Placement readiness
    readiness = calculate_placement_readiness(db, student, save_snapshot=False)
    readiness_score = readiness["overall_score"]
    coding_score = readiness["components"]["coding"]["score"]
    aptitude_score = readiness["components"]["aptitude"]["score"]

    # Decision logic based on configurable institutional criteria:
    # Priority 1: Segment D (Immediate Intervention) takes highest urgent precedence if critical risks exist
    if att_pct < 75.0 or backlogs > 0 or missing_assigns >= 3 or cgpa < 5.8:
        code = "D"
        reasons = []
        if att_pct < 75.0:
            reasons.append(f"Attendance {att_pct:.1f}% is below 75% limit")
        if backlogs > 0:
            reasons.append(f"{backlogs} active backlogs require immediate clearance")
        if missing_assigns >= 3:
            reasons.append(f"{missing_assigns} incomplete assignments")
        if cgpa < 5.8:
            reasons.append(f"CGPA {cgpa:.2f} is in critical range")
        reason_str = "; ".join(reasons)
    # Priority 2: Segment A (Top Performers)
    elif cgpa >= 8.2 and att_pct >= 85.0 and assign_comp_pct >= 85.0 and success_score >= 80.0:
        code = "A"
        reason_str = (
            f"Outstanding CGPA {cgpa:.2f}, {att_pct:.1f}% attendance, "
            f"and high overall success score of {success_score:.1f}/100."
        )
    # Priority 3: Segment C (Placement Ready)
    elif readiness_score >= 75.0 and coding_score >= 70.0 and aptitude_score >= 70.0 and cgpa >= 6.5:
        code = "C"
        reason_str = (
            f"High placement readiness ({readiness_score:.1f}%), coding benchmark achieved "
            f"({coding_score}%), and solid CGPA {cgpa:.2f}."
        )
    # Priority 4: Segment B (Academically Strong, Placement Weak)
    elif cgpa >= 7.0 and (readiness_score < 65.0 or coding_score < 60.0 or aptitude_score < 60.0):
        code = "B"
        reason_str = (
            f"Good academic CGPA of {cgpa:.2f}, but placement readiness ({readiness_score:.1f}%) "
            f"and coding/aptitude scores need focused training."
        )
    # Fallback to balanced development or Top Performer / Developing
    elif success_score >= 75.0:
        code = "A"
        reason_str = f"Strong multi-dimensional success score of {success_score:.1f}/100 with consistent records."
    else:
        code = "B"
        reason_str = f"Moderate CGPA of {cgpa:.2f} with opportunities to enhance technical interview readiness."

    segment_meta = SEGMENTS[code]

    if save_record:
        # Check if student segment exists
        existing = db.scalar(
            select(StudentSegment)
            .where(StudentSegment.student_id == student.id)
            .order_by(StudentSegment.assigned_at.desc())
            .limit(1)
        )
        if not existing or existing.segment_code != code:
            db.add(
                StudentSegment(
                    student_id=student.id,
                    segment_code=code,
                    segment_name=segment_meta["name"],
                    assignment_reason=reason_str,
                    is_primary=True,
                )
            )
            db.commit()

    return {
        "student_id": student.id,
        "segment_code": code,
        "segment_name": segment_meta["name"],
        "description": segment_meta["description"],
        "color": segment_meta["color"],
        "assignment_reason": reason_str,
        "metrics": {
            "cgpa": cgpa,
            "attendance_pct": att_pct,
            "success_score": success_score,
            "readiness_score": readiness_score,
            "coding_score": coding_score,
            "aptitude_score": aptitude_score,
            "backlogs": backlogs,
        },
    }


def get_segmentation_summary(db: Session, department_id: int | None = None) -> dict[str, Any]:
    """Provides segment distribution and student listings for faculty and administrators."""
    stmt = select(Student)
    if department_id:
        stmt = stmt.where(Student.department_id == department_id)
    students = db.scalars(stmt).all()

    segments_data: dict[str, list] = {"A": [], "B": [], "C": [], "D": []}
    for s in students:
        info = classify_student_segment(db, s, save_record=False)
        segments_data[info["segment_code"]].append({
            "id": s.id,
            "roll_no": s.roll_no,
            "name": s.name,
            "section": s.section,
            "semester": s.current_semester,
            "department": s.department.name if s.department else "",
            "reason": info["assignment_reason"],
            **info["metrics"],
        })

    total = len(students) or 1
    distribution = [
        {
            "code": code,
            "name": SEGMENTS[code]["name"],
            "count": len(items),
            "percentage": round(len(items) / total * 100.0, 1),
            "color": SEGMENTS[code]["color"],
            "description": SEGMENTS[code]["description"],
        }
        for code, items in segments_data.items()
    ]

    return {
        "total_students": len(students),
        "distribution": distribution,
        "segments": segments_data,
    }
