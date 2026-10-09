"""Administrator Portal Router: Institution-wide KPIs, Configurable Weights, Models, Users, and Exports."""

import csv
import io
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.db import get_db
from app.models.academic import Course, CourseResult, SemesterResult
from app.models.analytics import (
    AcademicRiskPrediction,
    Intervention,
    ModelMetadata,
    PlacementReadinessScore,
    StudentSuccessScore,
)
from app.models.engagement import FeedbackResponse
from app.models.enums import Role
from app.models.identity import Department, Faculty, Student, User
from app.services import student_data as sd
from app.services.academic_risk import predict_academic_risk, train_academic_risk_model
from app.services.placement_readiness import calculate_placement_readiness
from app.services.settings import (
    DEFAULT_PLACEMENT_READINESS_WEIGHTS,
    DEFAULT_SUCCESS_SCORE_WEIGHTS,
    DEFAULT_THRESHOLDS,
    get_placement_weights,
    get_success_score_weights,
    get_thresholds,
    set_setting,
)
from app.services.success_score import calculate_student_success_score

router = APIRouter(prefix="/admin", tags=["admin"])


class WeightsUpdateIn(BaseModel):
    success_score_weights: dict[str, float] | None = None
    placement_readiness_weights: dict[str, float] | None = None
    thresholds: dict[str, float] | None = None


class UserStatusUpdateIn(BaseModel):
    is_active: bool | None = None
    role: str | None = None


@router.get("/dashboard")
def admin_dashboard(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    total_students = db.scalar(select(func.count(Student.id))) or 0
    total_faculty = db.scalar(select(func.count(Faculty.id))) or 0
    total_departments = db.scalar(select(func.count(Department.id))) or 0

    all_students = db.scalars(select(Student)).all()

    # CGPA & Attendance metrics
    cgpa_list = []
    att_list = []
    success_scores = []
    readiness_scores = []
    high_risk_count = 0
    placement_eligible_count = 0

    for s in all_students:
        res = sd.results(db, s.id)
        if res.get("cgpa") is not None:
            cgpa_list.append(res["cgpa"])

        att = sd.attendance_report(db, s)
        pct = att.get("overall", {}).get("percentage")
        if pct is not None:
            att_list.append(pct)

        ss = calculate_student_success_score(db, s, save_snapshot=False)
        success_scores.append(ss["overall_score"])

        pr = calculate_placement_readiness(db, s, save_snapshot=False)
        readiness_scores.append(pr["overall_score"])

        plc = sd.placement(db, s, res, att)
        if plc.get("eligible"):
            placement_eligible_count += 1

        risk = predict_academic_risk(db, s, save_prediction=False)
        if risk["risk_category"] == "high":
            high_risk_count += 1

    avg_cgpa = round(sum(cgpa_list) / len(cgpa_list), 2) if cgpa_list else None
    avg_att = round(sum(att_list) / len(att_list), 1) if att_list else None
    avg_success = round(sum(success_scores) / len(success_scores), 1) if success_scores else None
    avg_readiness = round(sum(readiness_scores) / len(readiness_scores), 1) if readiness_scores else None

    # Intervention statistics
    total_interventions = db.scalar(select(func.count(Intervention.id))) or 0
    completed_interventions = db.scalar(
        select(func.count(Intervention.id)).where(Intervention.status == "completed")
    ) or 0
    intervention_rate = (
        round((completed_interventions / total_interventions) * 100.0, 1)
        if total_interventions > 0
        else 0.0
    )

    # Success score distribution buckets
    ss_buckets = {"< 60": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90+": 0}
    for score in success_scores:
        if score < 60:
            ss_buckets["< 60"] += 1
        elif score < 70:
            ss_buckets["60-69"] += 1
        elif score < 80:
            ss_buckets["70-79"] += 1
        elif score < 90:
            ss_buckets["80-89"] += 1
        else:
            ss_buckets["90+"] += 1

    # Readiness distribution
    ready_count = sum(1 for r in readiness_scores if r >= 75.0)
    dev_count = sum(1 for r in readiness_scores if 55.0 <= r < 75.0)
    need_imp_count = sum(1 for r in readiness_scores if r < 55.0)

    return {
        "kpis": {
            "total_students": total_students,
            "total_faculty": total_faculty,
            "total_departments": total_departments,
            "average_cgpa": avg_cgpa,
            "average_attendance": avg_att,
            "average_success_score": avg_success,
            "average_placement_readiness": avg_readiness,
            "placement_eligible_count": placement_eligible_count,
            "high_risk_students": high_risk_count,
            "total_interventions": total_interventions,
            "completed_interventions": completed_interventions,
            "intervention_completion_rate": intervention_rate,
        },
        "success_score_distribution": [{"range": k, "count": v} for k, v in ss_buckets.items()],
        "readiness_distribution": [
            {"category": "Placement Ready (75+)", "count": ready_count, "color": "emerald"},
            {"category": "Developing (55-74)", "count": dev_count, "color": "amber"},
            {"category": "Needs Improvement (<55)", "count": need_imp_count, "color": "rose"},
        ],
    }


@router.get("/settings")
def get_system_settings(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return {
        "success_score_weights": get_success_score_weights(db),
        "placement_readiness_weights": get_placement_weights(db),
        "thresholds": get_thresholds(db),
    }


@router.put("/settings")
def update_system_settings(
    body: WeightsUpdateIn,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    updated = {}
    if body.success_score_weights:
        updated["success_score_weights"] = set_setting(db, "success_score_weights", body.success_score_weights)
    if body.placement_readiness_weights:
        updated["placement_readiness_weights"] = set_setting(db, "placement_readiness_weights", body.placement_readiness_weights)
    if body.thresholds:
        updated["thresholds"] = set_setting(db, "thresholds", body.thresholds)
    return {"message": "Settings updated successfully", "settings": updated}


@router.get("/models")
def get_models_status(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    models = db.scalars(select(ModelMetadata).order_by(ModelMetadata.id.desc())).all()
    if not models:
        # Train once if metadata not yet created
        train_academic_risk_model(db)
        models = db.scalars(select(ModelMetadata).order_by(ModelMetadata.id.desc())).all()

    return [
        {
            "id": m.id,
            "model_name": m.model_name,
            "model_version": m.model_version,
            "algorithm": m.algorithm,
            "metrics": m.metrics,
            "feature_importances": m.feature_importances,
            "trained_at": m.trained_at.isoformat() if m.trained_at else None,
            "is_active": m.is_active,
        }
        for m in models
    ]


@router.post("/models/retrain")
def retrain_models(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = train_academic_risk_model(db)
    return {"message": "Academic risk machine learning model retrained successfully", "result": res}


@router.get("/users")
def list_users(
    role: str | None = None,
    search: str | None = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    stmt = select(User).order_by(User.id)
    if role:
        stmt = stmt.where(User.role == role)
    if search:
        stmt = stmt.where(User.email.ilike(f"%{search.strip()}%"))

    users = db.scalars(stmt).all()
    out = []
    for u in users:
        name = u.email
        extra = ""
        if u.role == Role.student:
            st = db.scalar(select(Student).where(Student.user_id == u.id))
            if st:
                name = st.name
                extra = f"{st.roll_no} | Sec {st.section}"
        elif u.role == Role.faculty:
            fac = db.scalar(select(Faculty).where(Faculty.user_id == u.id))
            if fac:
                name = fac.name
                extra = f"{fac.designation} | {fac.department.code}"

        out.append({
            "id": u.id,
            "email": u.email,
            "name": name,
            "role": u.role.value,
            "is_active": u.is_active,
            "extra": extra,
            "created_at": u.created_at.strftime("%Y-%m-%d"),
        })
    return out


@router.patch("/users/{user_id}")
def update_user_status(
    user_id: int,
    body: UserStatusUpdateIn,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    if body.is_active is not None:
        user.is_active = body.is_active
    if body.role:
        if body.role not in [r.value for r in Role]:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid role")
        user.role = Role(body.role)

    db.commit()
    return {"message": "User updated successfully"}


@router.get("/export")
def export_report(
    report_type: str = Query(default="students", pattern="^(students|interventions|departments)$"),
    format: str = Query(default="csv", pattern="^(csv|json)$"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if report_type == "students":
        students = db.scalars(select(Student).order_by(Student.roll_no)).all()
        rows = []
        for s in students:
            res = sd.results(db, s.id)
            att = sd.attendance_report(db, s)
            ss = calculate_student_success_score(db, s, save_snapshot=False)
            pr = calculate_placement_readiness(db, s, save_snapshot=False)
            risk = predict_academic_risk(db, s, save_prediction=False)

            rows.append({
                "Roll No": s.roll_no,
                "Name": s.name,
                "Department": s.department.code if s.department else "",
                "Semester": s.current_semester,
                "Section": s.section,
                "CGPA": res.get("cgpa", ""),
                "Attendance %": att.get("overall", {}).get("percentage", ""),
                "Success Score": ss["overall_score"],
                "Success Category": ss["score_category"],
                "Placement Readiness": pr["overall_score"],
                "Placement Category": pr["category"],
                "Academic Risk %": risk["risk_probability"],
                "Risk Category": risk["risk_category"],
            })

        if format == "json":
            return rows

        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=campus_students_report.csv"},
        )

    # fallback
    return {"message": f"Export report for {report_type}"}
