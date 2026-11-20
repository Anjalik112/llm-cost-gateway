# Prices in USD per 1 million tokens.
# Sources: console.groq.com/docs/models, ai.google.dev/pricing (checked 2026-11-20)
# gemini-3.6-flash doubles on 2027-01-01: input 1.50, output 7.50

MODEL_PRICES = {
    "openai/gpt-oss-20b": {"provider": "groq", "input_per_1m": 0.075, "output_per_1m": 0.30},
    "openai/gpt-oss-120b": {"provider": "groq", "input_per_1m": 0.15, "output_per_1m": 0.60},
    "gemini-3.5-flash-lite": {"provider": "gemini", "input_per_1m": 0.30, "output_per_1m": 2.50},
    "gemini-3.6-flash": {"provider": "gemini", "input_per_1m": 0.75, "output_per_1m": 3.75},
}

# Order matters: the first model is tried first, the next ones are fallbacks.
TIER_MODELS = {
    "simple": ["openai/gpt-oss-20b", "gemini-3.5-flash-lite"],
    "medium": ["openai/gpt-oss-120b", "gemini-3.5-flash-lite"],
    "hard": ["gemini-3.6-flash", "openai/gpt-oss-120b"],
}