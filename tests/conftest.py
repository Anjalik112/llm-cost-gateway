import pytest
from fastapi.testclient import TestClient

import app.db as db
from app.main import app
from app.router import Router
from tests.fakes import FakeCache, FakeProvider


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()

    app.state.router = Router(providers={
        "groq": FakeProvider("groq"),
        "gemini": FakeProvider("gemini"),
    })
    app.state.cache = FakeCache()

    return TestClient(app)