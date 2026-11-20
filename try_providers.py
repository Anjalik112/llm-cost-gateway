from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider

calls = [
    (GroqProvider(), "openai/gpt-oss-20b"),
    (GeminiProvider(), "gemini-3.5-flash-lite"),
    (GeminiProvider(), "gemini-3.5-flash"),
]

prompt = "Explain what an API is in one sentence."

for provider, model in calls:
    result = provider.generate(prompt, model)
    print(f"\n--- {result.provider} / {result.model} ---")
    print(result.text)
    print(f"input: {result.input_tokens}, output: {result.output_tokens}")