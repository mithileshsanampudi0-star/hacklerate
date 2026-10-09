from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


connect_args = {}
engine_kwargs = {}
if "sqlite" in settings.sqlalchemy_url:
    connect_args["check_same_thread"] = False
else:
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(settings.sqlalchemy_url, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)



def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
