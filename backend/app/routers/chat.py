"""Chat assistant router for grounded natural-language campus Q&A."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db import get_db
from app.models.identity import User
from app.services.chat_assistant import process_chat_query

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessageIn(BaseModel):
    message: str = Field(..., min_length=2, max_length=1000)


@router.post("/ask")
def chat_ask(
    body: ChatMessageIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = process_chat_query(db, user, body.message)
    return result
