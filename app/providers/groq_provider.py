
import os

from dotenv import load_dotenv
from groq import Groq
from app.providers.base import BaseProvider, LLMResponse

load_dotenv()


class GroqProvider(BaseProvider):
    name = "groq"

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in .env")
        self.client = Groq(api_key=api_key)

    def generate(self, prompt: str, model: str) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return LLMResponse(
            text=response.choices[0].message.content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            model=model,
            provider=self.name,
        )