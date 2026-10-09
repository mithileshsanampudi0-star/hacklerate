# Campus Portal: Student Academic Progress

A web portal with three role-based workspaces:

- **Students** see their attendance and attendance risk, exam marks, SGPA and CGPA for every semester and year, assignments, certifications, pending feedback forms, club activities, placement eligibility, and faculty remarks. They can also ask faculty for help.
- **Faculty** see every student's performance through a dashboard, an at-risk list, a filterable student list, and a full profile per student. They can write behaviour and academic remarks (visible to the student, or private) and answer students' help requests.
- **Administrators** see institution-wide analytics, manage users and scoring settings, review student segments, and inspect model-training metadata. The student academic-risk score itself is currently calculated by transparent rules.

The interface includes a saved light/dark appearance preference and adapts its workspace to each role.

**Stack:** React + Vite + TypeScript + Tailwind CSS, FastAPI, PostgreSQL. It deploys on the free tiers of Vercel, Render and Neon. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the schema, rules and deployment.

## Run locally

Requires Python 3.11+, Node 20+, and Docker (used only for the local Postgres).

```bash
docker compose up -d db
```

Then set up the backend:

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
alembic upgrade head
python seed.py                # demo data; `python seed.py --reset` to start over
uvicorn app.main:app --reload # http://localhost:8000/docs
```

Then the frontend, in another terminal:

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173 (proxies /api to :8000)
```

### Demo accounts

The seed creates 30 students in semester 5 (batch 2024), two faculty members, and an administrator. The emails and shared passwords are listed at the top of [backend/seed.py](backend/seed.py). For example, student `24cse007` is a deliberately at-risk profile, and `anjali.rao` and `kiran.mehta` are the faculty mentors for sections A and B.

## Tests

```bash
cd backend && python -m pytest -q
```

The tests cover:

- GPA, attendance-risk and placement maths
- auth and role separation
- hiding private remarks from students
- the feedback-form flow
- the help-request round trip
- faculty filters
- marks validation

They run on in-memory SQLite, so no database is needed.

## API at a glance

| Area | Endpoints |
|------|-----------|
| Auth | `POST /api/auth/login`, `POST /api/auth/refresh`, `GET /api/auth/me` |
| Student | `GET /api/student/me/{dashboard,attendance,marks,results,assignments,certifications,feedback-forms,activities,placement,remarks,help-requests,courses}`, `POST certifications`, `POST feedback-forms/{id}`, `POST help-requests`, `POST help-requests/{id}/replies` |
| Faculty | `GET /api/faculty/{dashboard,students,at-risk,students/{id},help-requests,courses}`, `POST students/{id}/remarks`, `POST help-requests/{id}/replies`, `PATCH help-requests/{id}`, `POST marks`, `POST attendance`, `POST results/publish`, `POST certifications/{id}/verify` |

Interactive docs: `http://localhost:8000/docs`.
