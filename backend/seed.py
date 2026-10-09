"""Load demo data: 1 department, 2 faculty, 30 students, semesters 1-4 completed and semester 5 in progress.

    python seed.py            # seeds only if the database is empty
    python seed.py --reset    # wipes all rows first (local development only)

Demo logins (all students share one password, both faculty share another):
    students: 24cse001@campus.edu ... 24cse030@campus.edu / Student@123
    faculty:  anjali.rao@campus.edu, kiran.mehta@campus.edu / Faculty@123
"""

import random
import sys
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db import Base, SessionLocal
from app.models import (
    Activity,
    ActivityLevel,
    ActivityType,
    Assignment,
    AssignmentSubmission,
    Attendance,
    AttendanceStatus,
    Certification,
    Club,
    ClubMembership,
    Course,
    Department,
    Enrollment,
    Exam,
    ExamMark,
    ExamType,
    Faculty,
    FacultyRemark,
    FeedbackForm,
    FeedbackResponse,
    HelpReply,
    HelpRequest,
    HelpStatus,
    Intervention,
    LMSActivity,
    ModelMetadata,
    Notification,
    PlacementCriteria,
    PlacementReadinessScore,
    PlacementRiskPrediction,
    RemarkCategory,
    RemarkVisibility,
    Role,
    Semester,
    SkillAssessment,
    Student,
    StudentProfile,
    StudentSegment,
    StudentSuccessScore,
    SubmissionStatus,
    User,
)
from app.services.academic_risk import predict_academic_risk, train_academic_risk_model
from app.services.interventions import create_intervention
from app.services.notifications import send_notification
from app.services.placement_readiness import calculate_placement_readiness
from app.services.placement_risk import predict_placement_risk
from app.services.results import publish_course_results
from app.services.segmentation import classify_student_segment
from app.services.success_score import calculate_student_success_score

STUDENT_PASSWORD = "Student@123"
FACULTY_PASSWORD = "Faculty@123"
ADMIN_PASSWORD = "Admin@123"
BATCH = 2024
CURRENT_SEM = 5
TODAY = date(2026, 10, 9)  # seed data is anchored to this date


SEMESTERS = [
    (1, "2024-25", date(2024, 8, 1), date(2024, 12, 15)),
    (2, "2024-25", date(2025, 1, 6), date(2025, 5, 20)),
    (3, "2025-26", date(2025, 7, 28), date(2025, 12, 12)),
    (4, "2025-26", date(2026, 1, 5), date(2026, 5, 18)),
    (5, "2026-27", date(2026, 7, 27), date(2026, 12, 11)),
]

COURSES = {
    1: [("MA101", "Engineering Mathematics I", 4), ("PH101", "Engineering Physics", 3),
        ("CS101", "Programming in C", 4), ("EE101", "Basic Electrical Engineering", 3),
        ("ME101", "Engineering Graphics", 2)],
    2: [("MA102", "Engineering Mathematics II", 4), ("CH102", "Engineering Chemistry", 3),
        ("CS102", "Data Structures", 4), ("EC102", "Digital Logic Design", 3),
        ("HS102", "Communication Skills", 2)],
    3: [("MA201", "Discrete Mathematics", 4), ("CS201", "Object Oriented Programming with Java", 4),
        ("CS202", "Computer Organization", 3), ("CS203", "Database Management Systems", 4),
        ("CS204", "Python Programming Lab", 2)],
    4: [("MA202", "Probability and Statistics", 3), ("CS205", "Design and Analysis of Algorithms", 4),
        ("CS206", "Operating Systems", 4), ("CS207", "Theory of Computation", 3),
        ("CS208", "Web Technologies", 3)],
    5: [("CS301", "Computer Networks", 4), ("CS302", "Machine Learning", 4),
        ("CS303", "Software Engineering", 3), ("CS304", "Compiler Design", 3),
        ("CS305", "Cloud Computing", 3)],
}

# (type, max marks, weightage %, days after semester start)
EXAM_PLAN = [
    (ExamType.internal1, 30, 15, 45),
    (ExamType.assignment, 20, 10, 60),
    (ExamType.internal2, 30, 15, 90),
    (ExamType.end_sem, 100, 60, 130),
]

FIRST = ["Aarav", "Diya", "Rohan", "Sneha", "Vikram", "Ananya", "Karthik", "Meera", "Arjun", "Priya",
         "Rahul", "Kavya", "Siddharth", "Ishita", "Aditya", "Neha", "Varun", "Pooja", "Nikhil", "Riya",
         "Harsha", "Tanvi", "Manish", "Shreya", "Akash", "Divya", "Suresh", "Lakshmi", "Yash", "Nandini"]
LAST = ["Reddy", "Sharma", "Iyer", "Patel", "Nair", "Gupta", "Rao", "Menon", "Singh", "Kumar"]

CERTS = [("Python for Data Science", "NPTEL"), ("AWS Certified Cloud Practitioner", "Amazon Web Services"),
         ("Machine Learning Specialization", "Coursera"), ("Introduction to Networks", "Cisco Networking Academy"),
         ("Google Data Analytics", "Google"), ("SQL (Intermediate)", "HackerRank"),
         ("Joy of Computing using Python", "NPTEL")]
CLUBS = [("Coding Club", "Technical"), ("Robotics Club", "Technical"), ("NSS Unit", "Social Service"),
         ("Literary Club", "Cultural"), ("Sports Council", "Sports"), ("Music Club", "Cultural")]
ACTIVITIES = [("Smart India Hackathon", ActivityType.hackathon, ActivityLevel.national),
              ("Inter-college Code Sprint", ActivityType.competition, ActivityLevel.state),
              ("Blood Donation Camp", ActivityType.nss, ActivityLevel.college),
              ("Annual Sports Meet - 400m", ActivityType.sports, ActivityLevel.college),
              ("Tech Fest Paper Presentation", ActivityType.event, ActivityLevel.college),
              ("Cultural Night - Group Dance", ActivityType.cultural, ActivityLevel.college),
              ("State Robotics Challenge", ActivityType.competition, ActivityLevel.state)]
ACHIEVEMENTS = ["Participant", "Participant", "Winner", "Runner-up", "Finalist", "Volunteer"]

COURSE_FEEDBACK_QUESTIONS = [
    {"id": "q1", "text": "The instructor explains concepts clearly", "type": "rating"},
    {"id": "q2", "text": "The pace of the course is appropriate", "type": "rating"},
    {"id": "q3", "text": "Doubts are addressed in and after class", "type": "rating"},
    {"id": "q4", "text": "Assignments help me understand the subject", "type": "rating"},
    {"id": "q5", "text": "Any suggestions for improvement?", "type": "text"},
]
FACILITY_QUESTIONS = [
    {"id": "q1", "text": "Library resources and timings", "type": "rating"},
    {"id": "q2", "text": "Lab equipment and internet availability", "type": "rating"},
    {"id": "q3", "text": "Classroom cleanliness and comfort", "type": "rating"},
    {"id": "q4", "text": "What should the college improve first?", "type": "text"},
]


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _class_days(start: date, end: date, weekdays: set[int]) -> list[date]:
    days, d = [], start
    while d <= end:
        if d.weekday() in weekdays:
            days.append(d)
        d += timedelta(days=1)
    return days


def seed(db: Session, n_students: int = 30, rng_seed: int = 42) -> None:
    rng = random.Random(rng_seed)
    student_hash = hash_password(STUDENT_PASSWORD)
    faculty_hash = hash_password(FACULTY_PASSWORD)

    # Admin user
    admin_hash = hash_password(ADMIN_PASSWORD)
    admin_user = User(email="admin@campus.edu", password_hash=admin_hash, role=Role.admin)
    db.add(admin_user)
    db.flush()

    dept = Department(code="CSE", name="Computer Science & Engineering")
    dept_ece = Department(code="ECE", name="Electronics & Communication Engineering")
    dept_mech = Department(code="MECH", name="Mechanical Engineering")
    db.add_all([dept, dept_ece, dept_mech])
    db.flush()

    faculty = []
    for emp, name, email, desig, d_id in [
        ("F001", "Dr. Anjali Rao", "anjali.rao@campus.edu", "Professor", dept.id),
        ("F002", "Prof. Kiran Mehta", "kiran.mehta@campus.edu", "Associate Professor", dept.id),
        ("F003", "Dr. Suresh Nair", "suresh.nair@campus.edu", "Professor", dept_ece.id),
        ("F004", "Dr. Ramesh Verma", "ramesh.verma@campus.edu", "Professor", dept_mech.id),
    ]:
        user = User(email=email, password_hash=faculty_hash, role=Role.faculty)
        db.add(user)
        db.flush()
        f = Faculty(user_id=user.id, emp_id=emp, name=name, department_id=d_id, designation=desig)
        db.add(f)
        faculty.append(f)
    db.flush()


    semesters = {}
    for number, year, start, end in SEMESTERS:
        s = Semester(number=number, academic_year=year, start_date=start, end_date=end)
        db.add(s)
        semesters[number] = s
    db.flush()

    courses: dict[int, list[tuple[Course, Faculty]]] = {}
    for number, items in COURSES.items():
        courses[number] = []
        for i, (code, name, credits) in enumerate(items):
            c = Course(code=code, name=name, credits=credits, department_id=dept.id, semester_number=number)
            db.add(c)
            courses[number].append((c, faculty[i % 2]))
    db.flush()

    # Students: an "ability" drives marks and a "regularity" drives attendance.
    students, ability, regularity = [], {}, {}
    for i in range(n_students):
        roll = f"24CSE{i + 1:03d}"
        user = User(email=f"{roll.lower()}@campus.edu", password_hash=student_hash, role=Role.student)
        db.add(user)
        db.flush()
        section = "A" if i < n_students / 2 else "B"
        s = Student(
            user_id=user.id,
            roll_no=roll,
            name=f"{FIRST[i % len(FIRST)]} {LAST[(i * 7) % len(LAST)]}",
            department_id=dept.id,
            batch_year=BATCH,
            current_semester=CURRENT_SEM,
            section=section,
            mentor_faculty_id=faculty[0 if section == "A" else 1].id,
        )
        db.add(s)
        db.flush()
        db.add(
            StudentProfile(
                student_id=s.id,
                tenth_pct=round(rng.uniform(62, 98), 1),
                twelfth_pct=round(rng.uniform(58, 97), 1),
                phone=f"9{rng.randint(100000000, 999999999)}",
                dob=date(2006, rng.randint(1, 12), rng.randint(1, 28)),
            )
        )
        students.append(s)
        ability[s.id] = rng.uniform(0.6, 0.95)
        regularity[s.id] = rng.uniform(0.8, 0.98)
    # A few deliberate at-risk profiles so the faculty views have something to show.
    for idx, a, r in [(6, 0.47, 0.66), (11, None, 0.7), (22, None, 0.78)]:
        if idx < len(students):
            if a is not None:
                ability[students[idx].id] = a  # likely backlogs
            regularity[students[idx].id] = r
    db.flush()

    # Enrollments, exams and marks for every semester
    enrollments: dict[tuple[int, int], Enrollment] = {}
    for number, offerings in courses.items():
        sem = semesters[number]
        for course, teacher in offerings:
            for s in students:
                e = Enrollment(student_id=s.id, course_id=course.id, semester_id=sem.id, faculty_id=teacher.id)
                db.add(e)
                enrollments[(s.id, course.id)] = e
            for etype, max_marks, weight, offset in EXAM_PLAN:
                exam_date = sem.start_date + timedelta(days=offset)
                exam = Exam(course_id=course.id, semester_id=sem.id, type=etype, max_marks=max_marks,
                            weightage=weight, exam_date=exam_date)
                db.add(exam)
                db.flush()
                if exam_date > TODAY:
                    continue  # not conducted yet
                for s in students:
                    score = _clamp(rng.gauss(ability[s.id], 0.09))
                    db.add(ExamMark(exam_id=exam.id, student_id=s.id, marks_obtained=round(score * max_marks)))
    db.flush()

    # Results for completed semesters, via the same code faculty use to publish
    for number in range(1, CURRENT_SEM):
        for course, _ in courses[number]:
            publish_course_results(db, course.id, semesters[number].id)

    # Attendance for the running semester: each course meets 3 weekdays a week
    sem = semesters[CURRENT_SEM]
    for idx, (course, _) in enumerate(courses[CURRENT_SEM]):
        days = _class_days(sem.start_date, TODAY - timedelta(days=1), {idx % 5, (idx + 2) % 5, (idx + 4) % 5})
        for s in students:
            e = enrollments[(s.id, course.id)]
            for d in days:
                r = rng.random()
                if r < regularity[s.id]:
                    status = AttendanceStatus.present
                elif r < regularity[s.id] + 0.01:
                    status = AttendanceStatus.od
                else:
                    status = AttendanceStatus.absent
                db.add(Attendance(enrollment_id=e.id, class_date=d, period=idx + 1, status=status))
    db.flush()

    # Assignments for the running semester
    for course, _ in courses[CURRENT_SEM]:
        past = Assignment(course_id=course.id, semester_id=sem.id, title=f"{course.code} Assignment 1",
                          description=f"Problem set on the first two units of {course.name}.",
                          due_date=date(2026, 9, 5), max_marks=20)
        upcoming = Assignment(course_id=course.id, semester_id=sem.id, title=f"{course.code} Assignment 2",
                              description=f"Mini case study for {course.name}.",
                              due_date=date(2026, 10, 20), max_marks=20)
        db.add_all([past, upcoming])
        db.flush()
        for s in students:
            if rng.random() < 0.88:
                db.add(AssignmentSubmission(
                    assignment_id=past.id, student_id=s.id,
                    submitted_at=datetime(2026, 9, rng.randint(1, 5), 18, tzinfo=timezone.utc),
                    marks=round(_clamp(rng.gauss(ability[s.id], 0.08)) * 20), status=SubmissionStatus.graded))
            if rng.random() < 0.3:
                db.add(AssignmentSubmission(
                    assignment_id=upcoming.id, student_id=s.id,
                    submitted_at=datetime(2026, 10, rng.randint(1, 8), 20, tzinfo=timezone.utc),
                    status=SubmissionStatus.submitted))

    # Certifications, clubs and activities
    clubs = [Club(name=n, category=c) for n, c in CLUBS]
    db.add_all(clubs)
    db.flush()
    for s in students:
        for title, issuer in rng.sample(CERTS, rng.randint(0, 3)):
            db.add(Certification(
                student_id=s.id, title=title, issuer=issuer,
                issue_date=date(rng.choice([2025, 2026]), rng.randint(1, 9), rng.randint(1, 28)),
                credential_url="https://example.com/verify/" + s.roll_no.lower(),
                verified_by=rng.choice([None, faculty[0].id, faculty[1].id])))
        for club in rng.sample(clubs, rng.randint(1, 2)):
            db.add(ClubMembership(student_id=s.id, club_id=club.id,
                                  role=rng.choice(["Member", "Member", "Coordinator", "Volunteer"]),
                                  joined_on=date(2024, rng.randint(8, 12), rng.randint(1, 28))))
        for title, atype, level in rng.sample(ACTIVITIES, rng.randint(0, 3)):
            db.add(Activity(student_id=s.id, club_id=None, title=title, type=atype, level=level,
                            achievement=rng.choice(ACHIEVEMENTS),
                            activity_date=date(rng.choice([2025, 2026]), rng.randint(1, 9), rng.randint(1, 28))))

    # Feedback forms for the running semester
    forms = []
    for course, teacher in courses[CURRENT_SEM]:
        forms.append(FeedbackForm(title=f"Mid-semester feedback: {course.name}", course_id=course.id,
                                  faculty_id=teacher.id, semester_id=sem.id, open_from=date(2026, 9, 25),
                                  due_date=date(2026, 10, 25), questions=COURSE_FEEDBACK_QUESTIONS))
    forms.append(FeedbackForm(title="Campus facilities survey", department_id=dept.id, semester_id=sem.id,
                              open_from=date(2026, 10, 1), due_date=date(2026, 10, 31),
                              questions=FACILITY_QUESTIONS))
    forms.append(FeedbackForm(title="Semester orientation feedback", department_id=dept.id, semester_id=sem.id,
                              open_from=date(2026, 7, 28), due_date=date(2026, 8, 15),
                              questions=FACILITY_QUESTIONS[:2]))
    db.add_all(forms)
    db.flush()
    for form in forms:
        rate = 0.95 if form.due_date < TODAY else 0.35
        for s in students:
            if rng.random() < rate:
                answers = {q["id"]: (rng.randint(3, 5) if q["type"] == "rating" else "") for q in form.questions}
                db.add(FeedbackResponse(form_id=form.id, student_id=s.id, answers=answers))

    # Placement criteria for the batch
    db.add(PlacementCriteria(batch_year=BATCH, min_cgpa=6.5, max_active_backlogs=0, min_attendance_pct=75,
                             min_10th_pct=60, min_12th_pct=60))

    # A few remarks and help threads
    remarks = [
        (0, 0, RemarkCategory.appreciation, "Excellent leadership during the Coding Club workshop.", RemarkVisibility.student),
        (6, 0, RemarkCategory.academic, "Needs to focus on clearing the pending backlogs. Meet me every Friday.", RemarkVisibility.student),
        (6, 0, RemarkCategory.behaviour, "Seems distracted lately; parents may need to be contacted.", RemarkVisibility.faculty_only),
        (11, 0, RemarkCategory.attendance, "Attendance is below 75% in multiple courses. Please attend regularly.", RemarkVisibility.student),
        (22, 1, RemarkCategory.attendance, "Attendance close to the limit in Computer Networks.", RemarkVisibility.student),
        (17, 1, RemarkCategory.appreciation, "Great project demo in Software Engineering.", RemarkVisibility.student),
    ]
    for si, fi, cat, text, vis in remarks:
        if si < len(students):
            db.add(FacultyRemark(student_id=students[si].id, faculty_id=faculty[fi].id, category=cat,
                                 remark=text, visibility=vis))

    cn, ml = courses[CURRENT_SEM][0], courses[CURRENT_SEM][1]
    threads = [
        (6, cn, "Struggling with subnetting problems",
         "I could not follow the subnetting examples from last week. Could you suggest practice material?",
         HelpStatus.in_progress,
         ["Please go through chapter 4 practice set and come to my cabin on Monday at 2 PM."]),
        (3, ml, "Doubt in gradient descent", "Why does the learning rate need to be small? My loss is exploding.",
         HelpStatus.resolved,
         ["Large steps overshoot the minimum. Try 0.01 and plot the loss per epoch.", "Thank you, it works now!"]),
        (11, None, "Need guidance on attendance shortage",
         "I was ill for two weeks. How do I apply for medical leave condonation?", HelpStatus.open, []),
    ]
    for si, offering, subject, message, status, replies in threads:
        if si >= len(students):
            continue
        s = students[si]
        teacher = offering[1] if offering else faculty[0 if s.section == "A" else 1]
        req = HelpRequest(student_id=s.id, course_id=offering[0].id if offering else None, subject=subject,
                          message=message, status=status, assigned_faculty_id=teacher.id)
        db.add(req)
        db.flush()
        for i, text in enumerate(replies):
            author = teacher.user_id if i % 2 == 0 else s.user_id
            db.add(HelpReply(request_id=req.id, author_user_id=author, message=text))

    db.flush()

    # ------------------ Analytics & AI Seed Data ------------------
    # 1. LMS Activity and Skill Assessments for all students
    for i, s in enumerate(students):
        is_at_risk = (i == 6)  # 24cse007
        logins = rng.randint(4, 9) if is_at_risk else rng.randint(28, 70)
        views = rng.randint(5, 11) if is_at_risk else rng.randint(22, 55)
        videos = rng.randint(3, 7) if is_at_risk else rng.randint(18, 42)
        completed = rng.randint(2, 4) if is_at_risk else rng.randint(8, 14)
        hours = round(rng.uniform(6.0, 14.0) if is_at_risk else rng.uniform(32.0, 72.0), 1)
        last_dt = datetime.now() - timedelta(days=rng.randint(6, 18) if is_at_risk else rng.randint(0, 3))

        db.add(LMSActivity(
            student_id=s.id,
            login_count=logins,
            course_views=views,
            videos_watched=videos,
            assignments_completed=completed,
            time_spent_hours=hours,
            last_active=last_dt,
        ))

        # Skill Assessments
        tech = round(rng.uniform(42.0, 56.0) if is_at_risk else rng.uniform(68.0, 95.0), 1)
        comm = round(rng.uniform(48.0, 60.0) if is_at_risk else rng.uniform(65.0, 92.0), 1)
        team = round(rng.uniform(52.0, 68.0) if is_at_risk else rng.uniform(70.0, 95.0), 1)
        lead = round(rng.uniform(40.0, 58.0) if is_at_risk else rng.uniform(65.0, 90.0), 1)
        prob = round(rng.uniform(44.0, 56.0) if is_at_risk else rng.uniform(68.0, 94.0), 1)
        apti = round(rng.uniform(46.0, 58.0) if is_at_risk else rng.uniform(65.0, 92.0), 1)
        mock = round(rng.uniform(42.0, 55.0) if is_at_risk else rng.uniform(65.0, 90.0), 1)

        db.add(SkillAssessment(
            student_id=s.id,
            technical_score=tech,
            communication_score=comm,
            teamwork_score=team,
            leadership_score=lead,
            problem_solving_score=prob,
            aptitude_score=apti,
            mock_interview_score=mock,
            assessment_date=date(2026, 9, 20),
            assessment_source="Faculty Evaluation & Mock Placement Drive",
            assessor_faculty_id=faculty[0 if s.section == "A" else 1].id,
        ))
    db.flush()

    # 2. Pre-calculate success scores, placement readiness, risk predictions, and segmentation
    for s in students:
        calculate_student_success_score(db, s, save_snapshot=True)
        calculate_placement_readiness(db, s, save_snapshot=True)
        predict_academic_risk(db, s, save_prediction=True)
        predict_placement_risk(db, s, save_prediction=True)
        classify_student_segment(db, s, save_record=True)

    # 3. Interventions for at-risk students
    if len(students) > 6:
        s_risk = students[6]
        create_intervention(
            db=db,
            student_id=s_risk.id,
            faculty_id=faculty[0].id,
            category="attendance",
            title="Mandatory Attendance Recovery Plan",
            description="Attendance has dropped to 68%. Student must attend next 12 consecutive classes.",
            urgency="critical",
            action_steps=[
                "Attend all CS301 and CS302 lectures without absence.",
                "Weekly Friday check-in with Dr. Anjali Rao.",
                "Submit medical documentation for past absences.",
            ],
            target_date=date(2026, 11, 15),
        )
        create_intervention(
            db=db,
            student_id=s_risk.id,
            faculty_id=faculty[0].id,
            category="academic",
            title="Remedial Backlog Mentoring",
            description="Clear pending semester backlogs through dedicated problem-solving sessions.",
            urgency="high",
            action_steps=[
                "Complete remedial question bank for Discrete Mathematics.",
                "Weekly doubt-clearing sessions on Algorithms.",
            ],
            target_date=date(2026, 11, 30),
        )

    # 4. Proactive notifications
    for s in students[:5]:
        send_notification(
            db=db,
            user_id=s.user_id,
            title="Placement Drive Registration Open",
            message="Campus placement drive registration is now live for eligible final-year candidates.",
            notif_type="placement_alert",
            severity="info",
            link_url="/student/placement",
        )
    if len(students) > 6:
        send_notification(
            db=db,
            user_id=students[6].user_id,
            title="Attendance Shortage Warning",
            message="Your attendance is currently below the mandatory 75% threshold in 2 courses. Immediate recovery required.",
            notif_type="attendance_alert",
            severity="critical",
            link_url="/student/attendance",
        )

    # 5. Train and evaluate the ML academic risk model
    train_academic_risk_model(db)

    db.commit()



def reset(db: Session) -> None:
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()


if __name__ == "__main__":
    from app.db import engine
    import app.models  # ensure models are registered
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        if "--reset" in sys.argv:
            reset(session)
        if session.scalar(select(func.count(User.id))):
            print("Database already has data; skipping seed (use --reset to wipe).")
        else:
            seed(session)
            print("Seeded demo data.")

