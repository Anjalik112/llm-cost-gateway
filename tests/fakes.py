from app.providers.base import BaseProvider, LLMResponse


class FakeProvider(BaseProvider):
    def __init__(self, name: str, fail: bool = False):
        self.name = name
        self.fail = fail
        self.calls = []

    def generate(self, prompt: str, model: str) -> LLMResponse:
        self.calls.append(model)
        if self.fail:
            raise ConnectionError(f"{self.name} is down")
        return LLMResponse(
            text=f"answer from {model}",
            input_tokens=10,
            output_tokens=20,
            model=model,
            provider=self.name,
        )