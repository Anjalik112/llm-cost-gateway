import os

from dotenv import load_dotenv
from google import genai

from app.providers.base import BaseProvider, LLMResponse

load_dotenv()


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in .env")
        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str, model: str) -> LLMResponse:
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
        )
        usage = response.usage_metadata
        answer_tokens = usage.candidates_token_count or 0
        thinking_tokens = usage.thoughts_token_count or 0

        return LLMResponse(
            text=response.text,
            input_tokens=usage.prompt_token_count or 0,
            output_tokens=answer_tokens + thinking_tokens,
            model=model,
            provider=self.name,
        )