import pytest

from app.router import AllProvidersFailed, Router, classify
from tests.fakes import FakeProvider


@pytest.mark.parametrize(
    "prompt, expected_tier",
    [
        ("What is an API?", "simple"),
        ("Summarise the benefits of remote work.", "medium"),
        ("Debug this: def add(a, b): return a - b", "hard"),
        ("x" * 600, "medium"),
        ("x" * 2500, "hard"),
    ],
)
def test_classify(prompt, expected_tier):
    assert classify(prompt) == expected_tier


@pytest.mark.xfail(reason="Known limitation: keyword matching uses substrings")
def test_decode_is_not_a_coding_task():
    assert classify("How do I decode a secret message?") == "simple"


def test_uses_first_model_when_it_works():
    groq = FakeProvider("groq")
    gemini = FakeProvider("gemini")
    router = Router(providers={"groq": groq, "gemini": gemini})

    result = router.route("What is an API?")

    assert result.response.provider == "groq"
    assert result.response.model == "openai/gpt-oss-20b"
    assert result.failed_attempts == []
    assert gemini.calls == []


def test_falls_back_to_other_provider_when_first_fails():
    groq = FakeProvider("groq", fail=True)
    gemini = FakeProvider("gemini")
    router = Router(providers={"groq": groq, "gemini": gemini})

    result = router.route("What is an API?")

    assert result.response.provider == "gemini"
    assert result.response.model == "gemini-3.5-flash-lite"
    assert len(result.failed_attempts) == 1
    assert "groq is down" in result.failed_attempts[0]


def test_raises_when_every_provider_fails():
    router = Router(providers={
        "groq": FakeProvider("groq", fail=True),
        "gemini": FakeProvider("gemini", fail=True),
    })

    with pytest.raises(AllProvidersFailed):
        router.route("What is an API?")


def test_cost_is_calculated_from_tokens():
    router = Router(providers={"groq": FakeProvider("groq"), "gemini": FakeProvider("gemini")})

    result = router.route("What is an API?")

    expected = 10 / 1_000_000 * 0.075 + 20 / 1_000_000 * 0.30
    assert result.cost_usd == pytest.approx(expected)