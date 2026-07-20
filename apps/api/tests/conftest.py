import os
from collections.abc import Iterator

import pytest

os.environ.setdefault("EPOINT_DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("EPOINT_SEED_MERCHANTS", "false")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from epoint_sandbox import db
from epoint_sandbox.models import Base, Merchant
from epoint_sandbox.services.seed import seed_default_merchants


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine, monkeypatch) -> sessionmaker[Session]:
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(db, "SessionLocal", factory)
    monkeypatch.setattr("epoint_sandbox.main.SessionLocal", factory)
    return factory


@pytest.fixture
def session(session_factory) -> Iterator[Session]:
    with session_factory() as s:
        yield s


@pytest.fixture
def merchants(session) -> list[Merchant]:
    created = seed_default_merchants(session)
    session.commit()
    return created


@pytest.fixture
def merchant(merchants) -> Merchant:
    return merchants[0]


@pytest.fixture
def client(session_factory, merchants) -> Iterator[TestClient]:
    from epoint_sandbox.main import app

    def override() -> Iterator[Session]:
        with session_factory() as s:
            try:
                yield s
                s.commit()
            except Exception:
                s.rollback()
                raise

    app.dependency_overrides[db.get_session] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
