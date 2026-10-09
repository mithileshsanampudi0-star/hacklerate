"""Placement Risk Prediction Engine with explainability and personalized recommendations."""

from datetime import datetime
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analytics import PlacementReadinessScore, PlacementRiskPrediction, SkillAssessment
from app.models.identity import Student
from app.services import student_data as sd
from app.services.placement_readiness import calculate_placement_readiness

MODEL_VERSION = "v1.1-placement-risk"


def predict_placement_risk(
    db: Session,
    student: Student,
    save_prediction: bool = True,
) -> dict[str, Any]:
    """Evaluates the risk that a student will not secure a placement offer."""
    # 1. Placement Readiness
    readiness = calculate_placement_readiness(db, student, save_snapshot=False)
    readiness_score = readiness["overall_score"]
    components = readiness["components"]

    # 2. Results & Eligibility
    res = sd.results(db, student.id)
    backlogs = res.get("active_backlogs", 0)
    cgpa = res.get("cgpa") or 6.5
    certs = sd.certifications(db, student.id)

    risk_points = 0.0
    key_factors = []
    recommendations = []

    # Coding impact
    coding_score = components["coding"]["score"]
    if coding_score < 50.0:
        risk_points += 30.0
        key_factors.append(f"Critical coding skill deficit ({coding_score}% in technical assessments)")
        recommendations.append("Mandatory enrollment in daily algorithmic problem-solving sprint")
    elif coding_score < 65.0:
        risk_points += 15.0
        key_factors.append(f"Moderate coding proficiency ({coding_score}%): needs competitive practice")
        recommendations.append("Practice 20 medium-level Data Structures problems on LeetCode")

    # Aptitude impact
    aptitude_score = components["aptitude"]["score"]
    if aptitude_score < 50.0:
        risk_points += 20.0
        key_factors.append(f"Aptitude score ({aptitude_score}%) is below company screening cutoff")
        recommendations.append("Complete weekly timed aptitude tests covering Quantitative & Logical Reasoning")
    elif aptitude_score < 65.0:
        risk_points += 10.0
        key_factors.append(f"Aptitude score ({aptitude_score}%) requires enhancement for tier-1 companies")

    # Mock Interview & Communication
    mock_score = components["mock_interview"]["score"]
    comm_score = components["communication"]["score"]
    if mock_score < 60.0 or comm_score < 60.0:
        risk_points += 20.0
        key_factors.append(f"Interview presentation score ({mock_score}%) and communication ({comm_score}%) need polish")
        recommendations.append("Attend mock HR interview simulation and technical articulation workshops")

    # Backlogs impact
    if backlogs > 0:
        risk_points += min(30.0, backlogs * 15.0)
        key_factors.append(f"{backlogs} active backlogs automatically disqualify student from 85% of campus drives")
        recommendations.append("Clear all backlogs in the upcoming supplementary examination window")

    # Low CGPA
    if cgpa < 6.5:
        risk_points += 15.0
        key_factors.append(f"CGPA ({cgpa:.2f}) does not meet the 6.5 minimum threshold of top recruiters")
        recommendations.append("Raise current semester SGPA above 7.5 to lift cumulative CGPA")

    # Certifications boost
    if len(certs) == 0:
        risk_points += 10.0
        key_factors.append("No verified industry certifications on profile")
        recommendations.append("Complete at least one recognized certification (AWS, Azure, GCP, or Oracle Java)")
    else:
        risk_points = max(5.0, risk_points - 10.0)

    # Base risk calculation inversely related to readiness
    base_from_readiness = max(0.0, 100.0 - readiness_score) * 0.4
    total_risk = round(min(100.0, max(5.0, (risk_points * 0.6) + base_from_readiness)), 1)

    if total_risk >= 65.0:
        category = "high"
    elif total_risk >= 35.0:
        category = "medium"
    else:
        category = "low"

    if not recommendations:
        recommendations.append("Maintain consistency and prepare for advanced system design questions.")

    result = {
        "risk_probability": total_risk,
        "risk_category": category,
        "readiness_score": readiness_score,
        "model_version": MODEL_VERSION,
        "key_factors": key_factors,
        "recommendations": recommendations,
        "prediction_timestamp": datetime.now(),
    }

    if save_prediction:
        rec = PlacementRiskPrediction(
            student_id=student.id,
            risk_probability=total_risk,
            risk_category=category,
            model_version=MODEL_VERSION,
            readiness_score=readiness_score,
            key_factors=key_factors,
            recommendations=recommendations,
        )
        db.add(rec)
        db.commit()

    return result
