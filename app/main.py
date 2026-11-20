from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.db import get_costs, init_db, log_call
from app.router import AllProvidersFailed, Router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.router = Router()
    yield


app = FastAPI(title="Cost-Aware LLM Gateway", lifespan=lifespan)


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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        result = app.state.router.route(request.prompt)
    except AllProvidersFailed as error:
        raise HTTPException(status_code=503, detail=str(error))

    log_call(result)

    return ChatResponse(
        answer=result.response.text,
        tier=result.tier,
        provider=result.response.provider,
        model=result.response.model,
        input_tokens=result.response.input_tokens,
        output_tokens=result.response.output_tokens,
        cost_usd=result.cost_usd,
        latency_ms=result.latency_ms,
        failed_attempts=result.failed_attempts,
    )


@app.get("/costs")
def costs():
    return get_costs()