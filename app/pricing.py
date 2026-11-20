from app.config import MODEL_PRICES


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    if model not in MODEL_PRICES:
        raise ValueError(f"No price configured for model '{model}'")

    price = MODEL_PRICES[model]
    input_cost = input_tokens / 1_000_000 * price["input_per_1m"]
    output_cost = output_tokens / 1_000_000 * price["output_per_1m"]
    return round(input_cost + output_cost, 8)