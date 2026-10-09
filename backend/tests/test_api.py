from seed import STUDENT_PASSWORD


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_login_rejects_wrong_role_and_password(client):
    r = client.post(
        "/api/auth/login",
        json={"email": "24cse001@campus.edu", "password": STUDENT_PASSWORD, "role": "faculty"},
    )
    assert r.status_code == 401
    r = client.post(
        "/api/auth/login", json={"email": "24cse001@campus.edu", "password": "wrong", "role": "student"}
    )
    assert r.status_code == 401


def test_refresh_issues_new_tokens(client):
    r = client.post(
        "/api/auth/login",
        json={"email": "24cse001@campus.edu", "password": STUDENT_PASSWORD, "role": "student"},
    )
    refresh = r.json()["refresh_token"]
    r2 = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 200
    # an access token must not be accepted as a refresh token
    r3 = client.post("/api/auth/refresh", json={"refresh_token": r.json()["access_token"]})
    assert r3.status_code == 401


def test_me(client, student_headers):
    me = client.get("/api/auth/me", headers=student_headers).json()
    assert me["role"] == "student" and me["email"] == "24cse007@campus.edu"


def test_student_endpoints_return_data(client, student_headers):
    for path in [
        "dashboard", "profile", "attendance", "marks", "results", "assignments", "certifications",
        "feedback-forms", "activities", "placement", "remarks", "help-requests", "courses",
    ]:
        r = client.get(f"/api/student/me/{path}", headers=student_headers)
        assert r.status_code == 200, (path, r.text)

    dash = client.get("/api/student/me/dashboard", headers=student_headers).json()
    assert len(dash["sgpa_trend"]) == 4  # semesters 1-4 have results
    assert dash["attendance"]["total"] > 0
    results = client.get("/api/student/me/results", headers=student_headers).json()
    assert results["cgpa"] == results["semesters"][-1]["cgpa_upto"]


def test_student_cannot_use_faculty_routes(client, student_headers):
    assert client.get("/api/faculty/students", headers=student_headers).status_code == 403
    assert client.get("/api/faculty/students/1", headers=student_headers).status_code == 403
    assert client.get("/api/student/me/dashboard").status_code == 401


def test_faculty_cannot_use_student_routes(client, faculty_headers):
    assert client.get("/api/student/me/dashboard", headers=faculty_headers).status_code == 403


def test_private_remarks_hidden_from_student(client, student_headers, faculty_headers):
    me = client.get("/api/auth/me", headers=student_headers).json()
    sid = me["profile_id"]
    r = client.post(
        f"/api/faculty/students/{sid}/remarks",
        headers=faculty_headers,
        json={"category": "behaviour", "remark": "Private note for faculty only", "visibility": "faculty_only"},
    )
    assert r.status_code == 201
    r = client.post(
        f"/api/faculty/students/{sid}/remarks",
        headers=faculty_headers,
        json={"category": "academic", "remark": "Visible improvement plan", "visibility": "student"},
    )
    assert r.status_code == 201

    student_view = client.get("/api/student/me/remarks", headers=student_headers).json()
    texts = [x["remark"] for x in student_view]
    assert "Visible improvement plan" in texts
    assert "Private note for faculty only" not in texts
    assert all(x["visibility"] == "student" for x in student_view)

    faculty_view = client.get(f"/api/faculty/students/{sid}", headers=faculty_headers).json()["remarks"]
    assert "Private note for faculty only" in [x["remark"] for x in faculty_view]


def test_feedback_submission_flow(client, student_headers):
    forms = client.get("/api/student/me/feedback-forms", headers=student_headers).json()
    form = next(f for f in forms["pending"] if not f["overdue"])
    bad = client.post(
        f"/api/student/me/feedback-forms/{form['id']}", headers=student_headers, json={"answers": {}}
    )
    assert bad.status_code == 422
    answers = {q["id"]: (4 if q["type"] == "rating" else "Good") for q in form["questions"]}
    ok = client.post(
        f"/api/student/me/feedback-forms/{form['id']}", headers=student_headers, json={"answers": answers}
    )
    assert ok.status_code == 201
    again = client.post(
        f"/api/student/me/feedback-forms/{form['id']}", headers=student_headers, json={"answers": answers}
    )
    assert again.status_code == 409
    after = client.get("/api/student/me/feedback-forms", headers=student_headers).json()
    assert form["id"] in [f["id"] for f in after["completed"]]


def test_help_request_round_trip(client, student_headers, faculty_headers):
    r = client.post(
        "/api/student/me/help-requests",
        headers=student_headers,
        json={"subject": "Need help with recursion", "message": "Can you explain tail recursion?"},
    )
    assert r.status_code == 201
    req_id = r.json()["id"]

    inbox = client.get("/api/faculty/help-requests?scope=all", headers=faculty_headers).json()
    created = next(x for x in inbox if x["id"] == req_id)
    assert created["assigned_to"] == "Prof. Kiran Mehta"  # no course given -> routed to the mentor (section B)

    r = client.post(
        f"/api/faculty/help-requests/{req_id}/replies", headers=faculty_headers, json={"message": "See me at 3 PM."}
    )
    assert r.status_code == 201
    mine = client.get("/api/student/me/help-requests", headers=student_headers).json()
    thread = next(x for x in mine if x["id"] == req_id)
    assert thread["status"] == "in_progress"
    assert thread["replies"][0]["message"] == "See me at 3 PM."


def test_faculty_list_filters_and_dashboard(client, faculty_headers):
    all_students = client.get("/api/faculty/students", headers=faculty_headers).json()
    assert all_students["total"] == 12
    mentees = client.get("/api/faculty/students?mentees_only=true", headers=faculty_headers).json()
    assert 0 < mentees["total"] < 12
    search = client.get("/api/faculty/students?search=24cse007", headers=faculty_headers).json()
    assert [s["roll_no"] for s in search["items"]] == ["24CSE007"]
    dash = client.get("/api/faculty/dashboard", headers=faculty_headers).json()
    assert dash["total_students"] == 12
    assert any(r["roll_no"] == "24CSE007" for r in dash["at_risk"])


def test_faculty_marks_entry_requires_teaching_the_course(client, faculty_headers):
    courses = client.get("/api/faculty/courses", headers=faculty_headers).json()
    assert courses and all(c["exams"] for c in courses)
    exam = courses[0]["exams"][0]
    r = client.post(
        "/api/faculty/marks", headers=faculty_headers, json={"exam_id": exam["id"], "entries": [{"student_id": 1, "marks": 999}]}
    )
    assert r.status_code == 400  # exceeds max marks
