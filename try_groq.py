from app.providers.groq_provider import GroqProvider

provider = GroqProvider()

for model in ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]:
    result = provider.generate("Explain what an API is in one sentence.", model)
    print(f"\n--- {model} ---")
    print(result.text)
    print(f"input tokens: {result.input_tokens}, output tokens: {result.output_tokens}")