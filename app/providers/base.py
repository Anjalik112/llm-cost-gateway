from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    model: str
    provider: str


class BaseProvider(ABC):
    name: str

    @abstractmethod
    def generate(self, prompt: str, model: str) -> LLMResponse:
        ...