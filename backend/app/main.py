import os
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, analytics, auth, chat, faculty, interventions, notifications, student

if (
    settings.jwt_secret == "dev-only-change-me"
    and "localhost" not in settings.sqlalchemy_url
    and "sqlite" not in settings.sqlalchemy_url
):
    raise RuntimeError("Set JWT_SECRET before running against a non-local database")


app = FastAPI(title="Smart Campus Analytics API", version="2.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")


@api.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


api.include_router(auth.router)
api.include_router(student.router)
api.include_router(faculty.router)
api.include_router(admin.router)
api.include_router(analytics.router)
api.include_router(interventions.router)
api.include_router(notifications.router)
api.include_router(chat.router)
app.include_router(api)

