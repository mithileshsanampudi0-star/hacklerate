"""Interventions Router: Actionable support plans, recommendations, and status workflows."""

from datetime import date
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_faculty, get_current_student, get_current_user, require_role
from app.db import get_db
from app.models.analytics import Intervention
from app.models.identity import Faculty, Student, User
from app.services.interventions import (
    create_intervention,
    generate_recommended_interventions,
    list_interventions_for_faculty,
    list_interventions_for_student,
    update_intervention_status,
)
from app.services.notifications import send_notification

router = APIRouter(prefix="/interventions", tags=["interventions"])


class InterventionCreateIn(BaseModel):
    student_id: int
    category: str = Field(..., pattern="^(academic|placement|attendance|counseling)$")
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5)
    urgency: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    action_steps: list[str] = Field(default_factory=list)
    target_date: date | None = None


class InterventionStatusUpdateIn(BaseModel):
    status: str = Field(..., pattern="^(pending|in_progress|completed|dismissed)$")
    notes: str | None = None
    outcome: str | None = None


@router.get("/recommendations")
def get_recommendations(
    student_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role.value == "student":
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        if not student:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Student profile not found")
        return generate_recommended_interventions(db, student)

    if not student_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "student_id is required for faculty/admin")
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    return generate_recommended_interventions(db, student)


@router.get("")
def list_interventions(
    status_filter: str | None = Query(default=None, alias="status"),
    faculty_id: int | None = None,
    department_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role.value == "student":
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        if not student:
            return []
        items = list_interventions_for_student(db, student.id)
        if status_filter:
            items = [i for i in items if i["status"] == status_filter]
        return items

    dept = department_id
    fac = faculty_id
    if user.role.value == "faculty":
        faculty_obj = db.scalar(select(Faculty).where(Faculty.user_id == user.id))
        if faculty_obj:
            dept = faculty_obj.department_id

    return list_interventions_for_faculty(db, faculty_id=fac, department_id=dept, status_filter=status_filter)


@router.post("", status_code=status.HTTP_201_CREATED)
def assign_intervention(
    body: InterventionCreateIn,
    user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db),
):
    student = db.get(Student, body.student_id)
    if not student:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")

    faculty_id = None
    if user.role.value == "faculty":
        fac = db.scalar(select(Faculty).where(Faculty.user_id == user.id))
        if fac:
            faculty_id = fac.id

    it = create_intervention(
        db=db,
        student_id=body.student_id,
        faculty_id=faculty_id,
        category=body.category,
        title=body.title,
        description=body.description,
        urgency=body.urgency,
        action_steps=body.action_steps,
        target_date=body.target_date,
    )

    # Proactively notify student
    send_notification(
        db=db,
        user_id=student.user_id,
        title=f"New Intervention Assigned: {body.title}",
        message=f"A new {body.category} action plan has been assigned to you with urgency '{body.urgency.upper()}'. Please check your action steps.",
        notif_type="intervention",
        severity="critical" if body.urgency in ("high", "critical") else "warning",
        link_url="/student/dashboard",
    )

    return {"id": it.id, "message": "Intervention assigned successfully"}


@router.patch("/{intervention_id}/status")
def update_status(
    intervention_id: int,
    body: InterventionStatusUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    it = db.get(Intervention, intervention_id)
    if not it:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Intervention not found")

    is_faculty = user.role.value in ("faculty", "admin")
    if user.role.value == "student":
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        if not student or it.student_id != student.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized to update this intervention")

    updated = update_intervention_status(
        db=db,
        intervention_id=intervention_id,
        status=body.status,
        notes=body.notes,
        outcome=body.outcome,
        is_faculty=is_faculty,
    )
    return {"id": updated.id, "status": updated.status, "message": "Status updated successfully"}
