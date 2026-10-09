from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import create_token, decode_token, get_current_user, verify_password
from app.db import get_db
from app.models import Faculty, Role, Student, User
from app.schemas import LoginIn, Me, RefreshIn, TokenPair

router = APIRouter(prefix="/auth", tags=["auth"])


def _tokens(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_token(user, "access"),
        refresh_token=create_token(user, "refresh"),
        role=user.role.value,
    )


@router.post("/login", response_model=TokenPair)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.email) == body.email.strip().lower()))
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if user.role.value != body.role:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"This is not a {body.role} account")
    return _tokens(user)


@router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    payload = decode_token(body.refresh_token, "refresh")
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return _tokens(user)


@router.get("/me", response_model=Me)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == Role.admin:
        return Me(id=user.id, email=user.email, role=user.role.value, name="System Administrator", profile_id=user.id)
    model = Student if user.role == Role.student else Faculty
    profile = db.scalar(select(model).where(model.user_id == user.id))
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile not found")
    return Me(id=user.id, email=user.email, role=user.role.value, name=profile.name, profile_id=profile.id)

