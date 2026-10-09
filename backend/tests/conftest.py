import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (registers tables)
from app.db import Base, get_db
from app.main import app
from seed import FACULTY_PASSWORD, STUDENT_PASSWORD, seed


@pytest.fixture(scope="session")
def session_factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as db:
        seed(db, n_students=12)
    return factory


@pytest.fixture(scope="session")
def client(session_factory):
    def override():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _login(client, email, password, role):
    r = client.post("/api/auth/login", json={"email": email, "password": password, "role": role})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def student_headers(client):
    return _login(client, "24cse007@campus.edu", STUDENT_PASSWORD, "student")


@pytest.fixture(scope="session")
def faculty_headers(client):
    return _login(client, "anjali.rao@campus.edu", FACULTY_PASSWORD, "faculty")
