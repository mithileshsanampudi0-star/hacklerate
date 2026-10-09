"""Placement Readiness Score calculation and skills evaluation."""

from datetime import datetime
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic import SemesterResult
from app.models.analytics import PlacementReadinessScore, SkillAssessment
from app.models.identity import Student
from app.services.settings import get_placement_weights, get_thresholds


def calculate_placement_readiness(
    db: Session,
    student: Student,
    save_snapshot: bool = True,
) -> dict[str, Any]:
    weights = get_placement_weights(db)
    thresholds = get_thresholds(db)

    # Latest skill assessment
    skill = db.scalar(
        select(SkillAssessment)
        .where(SkillAssessment.student_id == student.id)
        .order_by(SkillAssessment.assessment_date.desc(), SkillAssessment.id.desc())
        .limit(1)
    )

    # CGPA from latest SemesterResult or GPA calculation
    last_res = db.scalar(
        select(SemesterResult)
        .where(SemesterResult.student_id == student.id)
        .order_by(SemesterResult.semester_id.desc())
        .limit(1)
    )
    cgpa = last_res.cgpa_upto if last_res and last_res.cgpa_upto is not None else 7.0

    coding = skill.technical_score if skill and skill.technical_score is not None else 65.0
    aptitude = skill.aptitude_score if skill and skill.aptitude_score is not None else 65.0
    communication = skill.communication_score if skill and skill.communication_score is not None else 70.0
    mock = skill.mock_interview_score if skill and skill.mock_interview_score is not None else 65.0
    cgpa_norm = min(100.0, max(0.0, (cgpa / 10.0) * 100.0))

    components = {
        "coding": {"score": round(coding, 1), "weight": weights.get("coding", 0.30)},
        "aptitude": {"score": round(aptitude, 1), "weight": weights.get("aptitude", 0.20)},
        "communication": {"score": round(communication, 1), "weight": weights.get("communication", 0.15)},
        "mock_interview": {"score": round(mock, 1), "weight": weights.get("mock_interview", 0.15)},
        "cgpa": {"score": round(cgpa_norm, 1), "weight": weights.get("cgpa", 0.20)},
    }

    # Normalize weights sum
    total_w = sum(c["weight"] for c in components.values()) or 1.0
    overall = sum((c["score"] * c["weight"]) for c in components.values()) / total_w
    overall = round(min(100.0, max(0.0, overall)), 1)

    # Category
    ready_thresh = thresholds.get("placement_ready_score", 75.0)
    dev_thresh = thresholds.get("placement_developing_score", 55.0)
    if overall >= ready_thresh:
        category = "Placement Ready"
    elif overall >= dev_thresh:
        category = "Developing"
    else:
        category = "Needs Improvement"

    # Identify strengths & gaps
    strengths = []
    skill_gaps = []
    recommendations = []

    name_map = {
        "coding": "Coding & Algorithms",
        "aptitude": "Quantitative & Logical Aptitude",
        "communication": "Communication & Soft Skills",
        "mock_interview": "Mock Interview Technical Articulation",
        "cgpa": "Academic CGPA",
    }

    rec_map = {
        "coding": "Complete 3 medium Data Structures & Algorithms challenges weekly on LeetCode/HackerRank.",
        "aptitude": "Take weekly timed tests on quantitative reasoning and arithmetic problem solving.",
        "communication": "Enroll in the verbal presentation workshop and practice technical self-introductions.",
        "mock_interview": "Schedule a 1-on-1 mock technical interview session with department alumni mentors.",
        "cgpa": "Focus on upcoming semester assessments to boost cumulative academic grade point average.",
    }

    for key, data in components.items():
        label = name_map.get(key, key)
        if data["score"] >= 75.0:
            strengths.append(f"Strong in {label} ({data['score']}%)")
        elif data["score"] < 60.0:
            skill_gaps.append(f"{label} is below target benchmark ({data['score']}%)")
            recommendations.append(rec_map.get(key, f"Improve performance in {label}"))

    if not skill_gaps:
        recommendations.append("Continue maintaining consistency across competitive programming and system design challenges.")

    result = {
        "overall_score": overall,
        "category": category,
        "components": {k: {**v, "contribution": round(v["score"] * v["weight"] / total_w, 2)} for k, v in components.items()},
        "strengths": strengths,
        "skill_gaps": skill_gaps,
        "recommendations": recommendations,
        "calculated_at": datetime.now(),
    }

    if save_snapshot:
        snapshot = PlacementReadinessScore(
            student_id=student.id,
            overall_score=overall,
            category=category,
            coding_score=coding,
            aptitude_score=aptitude,
            communication_score=communication,
            mock_interview_score=mock,
            cgpa_score=cgpa_norm,
            strengths=strengths,
            skill_gaps=skill_gaps,
            recommendations=recommendations,
        )
        db.add(snapshot)
        db.commit()

    return result
