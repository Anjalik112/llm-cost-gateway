import pytest

from app.config import MODEL_PRICES, TIER_MODELS
from app.pricing import calculate_cost


def test_one_million_tokens_each_costs_input_plus_output_price():
    cost = calculate_cost("openai/gpt-oss-20b", 1_000_000, 1_000_000)
    assert cost == pytest.approx(0.075 + 0.30)


def test_zero_tokens_cost_nothing():
    assert calculate_cost("openai/gpt-oss-20b", 0, 0) == 0


def test_unknown_model_raises_error():
    with pytest.raises(ValueError):
        calculate_cost("model-that-does-not-exist", 10, 10)


def test_every_model_used_by_a_tier_has_a_price():
    for tier, models in TIER_MODELS.items():
        for model in models:
            assert model in MODEL_PRICES, f"{model} in tier '{tier}' has no price"
            