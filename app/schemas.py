from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)


class ChatResponse(BaseModel):
    answer: str
    tier: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    failed_attempts: list[str]
    cached: bool = False