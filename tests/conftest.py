import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.services import process_service


@pytest.fixture
def db_session():
    # Todas las conexiones comparten la misma DB en memoria
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def client(db_session, monkeypatch):
    """
    Cliente con DB aislada en memoria.
    El background task corre sincrónicamente usando la misma sesión de test
    """
    app.dependency_overrides[get_db] = lambda: db_session
    # Redirige la sesión que crea run_process_in_background hacia la DB de test
    monkeypatch.setattr(process_service, "SessionLocal", lambda: db_session)
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_bg(db_session, monkeypatch):
    """
    Cliente con DB aislada donde el background task no se ejecuta.
    Útil para tests.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    monkeypatch.setattr(process_service, "run_process_in_background", lambda pid: None)
    yield TestClient(app)
    app.dependency_overrides.clear()
