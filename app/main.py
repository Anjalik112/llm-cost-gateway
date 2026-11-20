import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.cache import ResponseCache
from app.config import DAILY_BUDGET_USD, REDIS_URL
from app.db import get_costs, get_today_spend, init_db, log_call
from app.router import AllProvidersFailed, Router
from app.schemas import ChatRequest, ChatResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.router = Router()
    app.state.cache = ResponseCache(REDIS_URL)
    yield


app = FastAPI(title="Cost-Aware LLM Gateway", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    start = time.perf_counter()

    cached = app.state.cache.get(request.prompt)
    if cached is not None:
        response = ChatResponse(**cached).model_copy(update={
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "latency_ms": int((time.perf_counter() - start) * 1000),
            "failed_attempts": [],
            "cached": True,
        })
        log_call(response)
        return response

    if get_today_spend() >= DAILY_BUDGET_USD:
        raise HTTPException(
            status_code=429,
            detail=f"Daily budget of ${DAILY_BUDGET_USD} reached. Try again tomorrow.",
        )

    try:
        result = app.state.router.route(request.prompt)
    except AllProvidersFailed as error:
        raise HTTPException(status_code=503, detail=str(error))

    response = ChatResponse(
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
    log_call(response)
    app.state.cache.set(request.prompt, response.model_dump())
    return response


@app.get("/costs")
def costs():
    return get_costs()