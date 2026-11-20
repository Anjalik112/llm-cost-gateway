import time
from dataclasses import dataclass, field

from app.config import MODEL_PRICES, TIER_MODELS
from app.pricing import calculate_cost
from app.providers.base import BaseProvider, LLMResponse
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider

HARD_KEYWORDS = ["code", "debug", "analyse", "analyze", "step by step", "prove", "architecture", "compare"]
MEDIUM_KEYWORDS = ["summarise", "summarize", "explain in detail", "rewrite", "list"]


def classify(prompt: str) -> str:
    text = prompt.lower()
    if len(prompt) > 2000 or any(word in text for word in HARD_KEYWORDS):
        return "hard"
    if len(prompt) > 500 or any(word in text for word in MEDIUM_KEYWORDS):
        return "medium"
    return "simple"


@dataclass
class RouteResult:
    response: LLMResponse
    tier: str
    cost_usd: float
    latency_ms: int
    failed_attempts: list[str] = field(default_factory=list)


class AllProvidersFailed(Exception):
    pass


class Router:
    def __init__(self):
        self.providers: dict[str, BaseProvider] = {
            "groq": GroqProvider(),
            "gemini": GeminiProvider(),
        }

    def route(self, prompt: str) -> RouteResult:
        tier = classify(prompt)
        failed_attempts = []

        for model in TIER_MODELS[tier]:
            provider = self.providers[MODEL_PRICES[model]["provider"]]
            start = time.perf_counter()
            try:
                response = provider.generate(prompt, model)
            except Exception as error:
                failed_attempts.append(f"{model}: {type(error).__name__}: {error}")
                continue

            latency_ms = int((time.perf_counter() - start) * 1000)
            cost = calculate_cost(model, response.input_tokens, response.output_tokens)
            return RouteResult(response, tier, cost, latency_ms, failed_attempts)

        raise AllProvidersFailed(f"All models failed for tier '{tier}': {failed_attempts}")