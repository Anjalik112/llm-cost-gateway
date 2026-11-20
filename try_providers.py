from app.pricing import calculate_cost
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider

calls = [
    (GroqProvider(), "openai/gpt-oss-20b"),
    (GeminiProvider(), "gemini-3.5-flash-lite"),
    (GeminiProvider(), "gemini-3.6-flash"),
]

prompt = "Explain what an API is in one sentence."

for provider, model in calls:
    result = provider.generate(prompt, model)
    cost = calculate_cost(result.model, result.input_tokens, result.output_tokens)
    print(f"\n--- {result.provider} / {result.model} ---")
    print(result.text)
    print(f"input: {result.input_tokens}, output: {result.output_tokens}, cost: ${cost:.8f}")