from app.router import Router
from tests.fakes import FakeProvider

PROMPT = {"prompt": "What is an API?"}


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_returns_answer_and_cost(client):
    response = client.post("/chat", json=PROMPT)

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "answer from openai/gpt-oss-20b"
    assert body["tier"] == "simple"
    assert body["provider"] == "groq"
    assert body["cached"] is False
    assert body["cost_usd"] > 0


def test_second_identical_request_is_cached_and_free(client):
    client.post("/chat", json=PROMPT)
    response = client.post("/chat", json=PROMPT)

    body = response.json()
    assert body["cached"] is True
    assert body["cost_usd"] == 0
    assert body["input_tokens"] == 0


def test_costs_counts_calls_and_cache_hits(client):
    client.post("/chat", json=PROMPT)
    client.post("/chat", json=PROMPT)

    rows = client.get("/costs").json()

    assert len(rows) == 1
    assert rows[0]["calls"] == 2
    assert rows[0]["cache_hits"] == 1


def test_empty_prompt_is_rejected(client):
    response = client.post("/chat", json={"prompt": ""})

    assert response.status_code == 422


def test_budget_reached_returns_429(client, monkeypatch):
    monkeypatch.setattr("app.main.DAILY_BUDGET_USD", 0.0)

    response = client.post("/chat", json=PROMPT)

    assert response.status_code == 429
    assert "budget" in response.json()["detail"].lower()


def test_cached_answer_still_served_when_budget_reached(client, monkeypatch):
    client.post("/chat", json=PROMPT)
    monkeypatch.setattr("app.main.DAILY_BUDGET_USD", 0.0)

    response = client.post("/chat", json=PROMPT)

    assert response.status_code == 200
    assert response.json()["cached"] is True


def test_all_providers_down_returns_503(client):
    client.app.state.router = Router(providers={
        "groq": FakeProvider("groq", fail=True),
        "gemini": FakeProvider("gemini", fail=True),
    })

    response = client.post("/chat", json=PROMPT)

    assert response.status_code == 503