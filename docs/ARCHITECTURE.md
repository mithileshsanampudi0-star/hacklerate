# Architecture

## Overview

```
                 ┌──────────────────────────────┐
  Browser ──────▶│ Vercel (free)                │  React + Vite static build
  (student /     │ SPA, all routes → index.html │  VITE_API_URL = Render URL
   faculty)      └──────────────┬───────────────┘
                                │ HTTPS  fetch /api/*  (Authorization: Bearer <JWT>)
                                ▼
                 ┌──────────────────────────────┐
                 │ Render Web Service (free)    │  FastAPI + Uvicorn in Docker
                 │ /api/auth  /api/student/me   │  alembic upgrade head on boot
                 │ /api/faculty  /api/health    │  CORS limited to the Vercel origin
                 └──────────────┬───────────────┘
                                │ TLS (sslmode=require), pooled connection
                                ▼
                 ┌──────────────────────────────┐
                 │ Neon PostgreSQL (free)       │  tables + reporting views
                 └──────────────────────────────┘
```

| Layer    | Tech                                                   | Folder      |
|----------|--------------------------------------------------------|-------------|
| Frontend | React 18, TypeScript, Vite, React Router, TanStack Query, Recharts, Tailwind CSS | `frontend/` |
| API      | FastAPI, SQLAlchemy 2.0, Pydantic v2, PyJWT, bcrypt    | `backend/app` |
| Database | PostgreSQL 16, Alembic migrations                      | `backend/alembic` |

## Backend layout

```
app/
  main.py              FastAPI app, CORS, /api router
  config.py            settings from env (DATABASE_URL, JWT_SECRET, CORS_ORIGINS)
  db.py                engine, session, Base
  core/security.py     bcrypt, JWT issue/verify, require_role(), current student/faculty
  models/              ORM tables, grouped by domain
  schemas/             request bodies (Pydantic)
  services/
    gpa.py             SGPA / CGPA / year GPA, grade scale, backlogs   (pure functions)
    attendance.py      percentage, risk level, classes needed / can skip (pure functions)
    placement.py       eligibility checks against batch criteria       (pure functions)
    results.py         marks → course grade → semester_results cache
    student_data.py    read-side queries shared by student and faculty routes
    analytics modules  scoring, risk, readiness, segmentation, trends, insights
    engagement modules interventions, notifications, chat assistant
  routers/             auth, student, faculty, admin, analytics, chat,
                       interventions, notifications
```

The student and faculty routers both call `services/student_data.py`, so a student and their teachers always see the same numbers.

The React app has separate student, faculty, and administrator route groups under `frontend/src/pages/`, shared UI and navigation under `frontend/src/components/`, and role-aware authentication/API clients under `frontend/src/auth/` and `frontend/src/api/`. The light/dark preference is saved in browser local storage.

## Security model

- **Login.** `POST /api/auth/login {email, password, role}` returns a 30-minute access JWT and a 7-day refresh JWT. Passwords are hashed with bcrypt.
- **Token storage.** The frontend keeps the access token in memory and the refresh token in `localStorage`. On a `401` it calls `/auth/refresh` once and retries the request.
- **Role checks.** `require_role("student" | "faculty")` guards every router. Student routes never take a student id from the URL; the student always comes from the token, so one student can't read another's data.
- **Remarks.** Faculty remarks have `visibility = student | faculty_only`. Students only receive `student` remarks.
- **Data entry.** Faculty marks, attendance and result endpoints check that the faculty member teaches that course offering.
- **Secret guard.** The API refuses to start against a non-local database while `JWT_SECRET` is still the development default.

## Database

### Main tables

**Identity**
- `users`: email, password hash, role enum
- `students`: roll number, batch, current semester, section, mentor (→ faculty)
- `faculty`: employee id, designation
- `departments`
- `student_profile`: 10th and 12th percentages, phone

**Academic**
- `semesters`
- `courses`
- `enrollments`: student × course × semester, plus the teaching faculty
- `attendance`: one row per enrollment, date and period; status is `present | absent | od | medical`
- `exams`: internal1, internal2, assignment, lab and end_sem, each with max marks and weightage
- `exam_marks`
- `course_results`: final grade per enrollment
- `semester_results`: cached SGPA and CGPA per semester

**Engagement**
- `assignments`, `assignment_submissions`
- `certifications`: `verified_by` → faculty
- `clubs`, `club_memberships`, `activities`
- `feedback_forms`: questions stored as JSONB; a form is either course-specific or department-wide
- `feedback_responses`: unique per (form, student)
- `faculty_remarks`
- `help_requests`, `help_replies`
- `placement_criteria`: one row per batch

### Views

- `v_attendance_summary`: attended, total and percentage per student per course per semester.
- `v_student_overview`: one row per student with CGPA, current-semester attendance, active backlogs and submitted assignments. Useful for reports and BI tools.

## Business rules

| Rule | Definition |
|------|------------|
| Grade scale | O 90+ (10), A+ 80+ (9), A 70+ (8), B+ 60+ (7), B 50+ (6), C 45+ (5), P 40+ (4), F (0) |
| SGPA | Σ(credits × points) / Σ credits for the semester; an F counts as 0 |
| CGPA | Same formula, using the best attempt of each course |
| Year GPA | Same formula over that year's two semesters |
| Course total | Σ (marks / max × weightage); weightages: I1 15, I2 15, assignment 10, end-sem 60 |
| Attendance risk | safe ≥ 85%, warning 75–85%, critical < 75%; OD and medical count as present |
| Classes needed | ceil((75·total − 100·attended) / 25) |
| Placement | CGPA, active backlogs, attendance, 10th % and 12th % against `placement_criteria` |

## Deploying on the free tier

### 1. Database (Neon)

1. Create a project at neon.tech.
2. Copy the **pooled** connection string. It looks like `postgresql://user:pass@ep-xxx-pooler.region.aws.neon.tech/db?sslmode=require`.

### 2. API (Render)

1. Push this repository to GitHub.
2. In Render, choose **New → Blueprint** and pick the repo. It reads `render.yaml`.
3. Set these environment variables:
   - `DATABASE_URL`: the Neon string. The `postgresql://` prefix is rewritten to the psycopg driver automatically.
   - `CORS_ORIGINS`: your Vercel URL. Fill this in after step 3, then redeploy.
   - `JWT_SECRET`: auto-generated by the blueprint.
   - `SEED_DEMO`: `true` loads demo data the first time. Set it to `false` for real use.
4. Each boot runs `alembic upgrade head`. Check that `https://<service>.onrender.com/api/health` returns `{"status":"ok"}`.

### 3. Frontend (Vercel)

1. Import the repo in Vercel and set **Root Directory** to `frontend`. The Vite framework preset is detected.
2. Add the environment variable `VITE_API_URL=https://<service>.onrender.com`.
3. Deploy. `vercel.json` rewrites every path to `index.html` so deep links work.

### Free-tier limits

- **Render sleep.** A free Render service sleeps after about 15 minutes idle, and the first request afterwards takes around 30–50 seconds. If the server can't be reached, the frontend shows a "server may be waking up" message.
- **Neon autosuspend.** Neon suspends compute when idle; it resumes on the next query, usually in under a second.
- **Upgrade path.** Move Render to a paid instance (no sleep) and Neon to a paid plan (more storage and branches). The code stays the same.

## CI

`.github/workflows/ci.yml` runs the backend tests (SQLite in memory) and the frontend type-check and build on every push. Vercel and Render redeploy automatically from the default branch.
