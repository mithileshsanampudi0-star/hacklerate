"""Tests for smart campus analytics: success scores, risk predictions,
placement readiness, interventions, notifications, admin portal, and campus assistant.
"""

import pytest
from seed import ADMIN_PASSWORD, FACULTY_PASSWORD, STUDENT_PASSWORD


@pytest.fixture(scope="session")
def admin_headers(client):
    r = client.post(
        "/api/auth/login",
        json={"email": "admin@campus.edu", "password": ADMIN_PASSWORD, "role": "admin"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_admin_dashboard_kpis(client, admin_headers):
    r = client.get("/api/admin/dashboard", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    kpis = data["kpis"]
    assert kpis["total_students"] > 0
    assert kpis["total_faculty"] > 0
    assert "average_cgpa" in kpis
    assert "average_success_score" in kpis
    assert "average_placement_readiness" in kpis
    assert len(data["success_score_distribution"]) > 0
    assert len(data["readiness_distribution"]) > 0


def test_admin_settings_update(client, admin_headers):
    # Fetch current settings
    r = client.get("/api/admin/settings", headers=admin_headers)
    assert r.status_code == 200
    settings = r.json()
    assert "success_score_weights" in settings
    assert settings["success_score_weights"]["cgpa"] == 0.30

    # Update weights
    update_payload = {
        "success_score_weights": {
            "cgpa": 0.35,
            "attendance": 0.20,
            "lms": 0.15,
            "assignments": 0.10,
            "certifications": 0.10,
            "placement": 0.05,
            "feedback": 0.05,
        }
    }
    r2 = client.put("/api/admin/settings", headers=admin_headers, json=update_payload)
    assert r2.status_code == 200

    # Verify update persisted
    r3 = client.get("/api/admin/settings", headers=admin_headers)
    assert r3.json()["success_score_weights"]["cgpa"] == 0.35


def test_student_success_score_breakdown(client, student_headers):
    r = client.get("/api/analytics/student/success-score", headers=student_headers)
    assert r.status_code == 200
    data = r.json()
    assert 0 <= data["overall_score"] <= 100
    assert data["score_category"] in ("Excellent", "Good", "Average", "At Risk")
    breakdown = data["breakdown"]
    assert "cgpa" in breakdown
    assert "attendance" in breakdown
    assert "lms" in breakdown
    assert "assignments" in breakdown
    assert "contribution" in breakdown["cgpa"]


def test_placement_readiness_and_skills(client, student_headers, faculty_headers):
    # Student reads readiness
    r = client.get("/api/analytics/student/placement-readiness", headers=student_headers)
    assert r.status_code == 200
    pr = r.json()
    assert 0 <= pr["overall_score"] <= 100
    assert pr["category"] in ("Placement Ready", "Developing", "Needs Improvement")
    assert "components" in pr
    assert "strengths" in pr
    assert "skill_gaps" in pr

    # Student reads skills profile
    r_skills = client.get("/api/analytics/student/skills", headers=student_headers)
    assert r_skills.status_code == 200
    assert "technical" in r_skills.json()

    # Faculty adds a new skill assessment
    assess_payload = {
        "student_id": 1,
        "technical_score": 88.0,
        "communication_score": 85.0,
        "teamwork_score": 90.0,
        "leadership_score": 82.0,
        "problem_solving_score": 86.0,
        "aptitude_score": 80.0,
        "mock_interview_score": 85.0,
        "assessment_source": "Placement Mock Drive",
    }
    r_post = client.post("/api/analytics/skills", headers=faculty_headers, json=assess_payload)
    assert r_post.status_code == 201


def test_academic_and_placement_risk_predictions(client, student_headers):
    # Academic risk
    r_acad = client.get("/api/analytics/student/academic-risk", headers=student_headers)
    assert r_acad.status_code == 200
    acad = r_acad.json()
    assert 0 <= acad["risk_probability"] <= 100
    assert acad["risk_category"] in ("low", "medium", "high")
    assert acad["model_version"] == "rules-v1.2"
    assert len(acad["contributing_factors"]) > 0
    assert len(acad["suggested_interventions"]) > 0

    # Placement risk
    r_plc = client.get("/api/analytics/student/placement-risk", headers=student_headers)
    assert r_plc.status_code == 200
    plc = r_plc.json()
    assert 0 <= plc["risk_probability"] <= 100
    assert plc["risk_category"] in ("low", "medium", "high")
    assert "key_factors" in plc
    assert "recommendations" in plc


def test_segmentation_and_insights(client, faculty_headers):
    # Segmentation
    r_seg = client.get("/api/analytics/segmentation", headers=faculty_headers)
    assert r_seg.status_code == 200
    seg = r_seg.json()
    assert len(seg["distribution"]) == 4  # Segments A, B, C, D
    assert "segments" in seg

    # Smart insights
    r_ins = client.get("/api/analytics/smart-insights", headers=faculty_headers)
    assert r_ins.status_code == 200
    insights = r_ins.json()
    assert isinstance(insights, list)
    if insights:
        assert "severity" in insights[0]
        assert "recommendation" in insights[0]


def test_interventions_workflow(client, student_headers, faculty_headers):
    # Student reads recommendations
    r_rec = client.get("/api/interventions/recommendations", headers=student_headers)
    assert r_rec.status_code == 200
    recs = r_rec.json()
    assert len(recs) > 0
    assert "action_steps" in recs[0]

    # Get student id
    me = client.get("/api/auth/me", headers=student_headers).json()
    sid = me["profile_id"]

    # Faculty assigns an intervention
    it_payload = {
        "student_id": sid,
        "category": "academic",
        "title": "Data Structures Supplementary Coaching",
        "description": "Weekly tutoring to prepare for end-semester algorithm assessment.",
        "urgency": "high",
        "action_steps": ["Complete module 3 practice problems", "Review dynamic programming tree problems"],
    }
    r_assign = client.post("/api/interventions", headers=faculty_headers, json=it_payload)
    assert r_assign.status_code == 201
    it_id = r_assign.json()["id"]


    # Student updates status
    r_patch = client.patch(
        f"/api/interventions/{it_id}/status",
        headers=student_headers,
        json={"status": "in_progress", "notes": "Started module 3 practice"},
    )
    assert r_patch.status_code == 200
    assert r_patch.json()["status"] == "in_progress"


def test_notifications_flow(client, student_headers):
    # Fetch notifications
    r_notif = client.get("/api/notifications", headers=student_headers)
    assert r_notif.status_code == 200
    data = r_notif.json()
    assert "unread_count" in data
    assert "items" in data

    if data["items"]:
        nid = data["items"][0]["id"]
        # Mark single as read
        r_read = client.patch(f"/api/notifications/{nid}/read", headers=student_headers)
        assert r_read.status_code == 200

    # Mark all as read
    r_all = client.post("/api/notifications/read-all", headers=student_headers)
    assert r_all.status_code == 200


def test_ai_chat_assistant_rbac(client, student_headers, faculty_headers):
    # Student asks about success score
    r_stu = client.post(
        "/api/chat/ask",
        headers=student_headers,
        json={"message": "What is my success score breakdown?"},
    )
    assert r_stu.status_code == 200
    assert "Student Success Score" in r_stu.json()["answer"]

    # Student asks about attendance
    r_att = client.post(
        "/api/chat/ask",
        headers=student_headers,
        json={"message": "What is my attendance and how many classes do I need to attend?"},
    )
    assert r_att.status_code == 200
    assert "attendance" in r_att.json()["answer"].lower()

    # Faculty asks about at-risk students
    r_fac = client.post(
        "/api/chat/ask",
        headers=faculty_headers,
        json={"message": "Which students need immediate intervention?"},
    )
    assert r_fac.status_code == 200
    assert "Risk" in r_fac.json()["answer"] or "student" in r_fac.json()["answer"].lower()

    # Faculty asks for department comparison
    r_dept = client.post(
        "/api/chat/ask",
        headers=faculty_headers,
        json={"message": "Which department has the highest average CGPA?"},
    )
    assert r_dept.status_code == 200
    assert "Department" in r_dept.json()["answer"]
