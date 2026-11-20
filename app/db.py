import sqlite3
from datetime import datetime, timezone

from app.schemas import ChatResponse

DB_PATH = "gateway.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            tier TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            cost_usd REAL NOT NULL,
            latency_ms INTEGER NOT NULL,
            fallback_count INTEGER NOT NULL,
            cached INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def log_call(response: ChatResponse):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO calls (created_at, tier, provider, model, input_tokens,
                           output_tokens, cost_usd, latency_ms, fallback_count, cached)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            response.tier,
            response.provider,
            response.model,
            response.input_tokens,
            response.output_tokens,
            response.cost_usd,
            response.latency_ms,
            len(response.failed_attempts),
            int(response.cached),
        ),
    )
    conn.commit()
    conn.close()


def get_today_spend() -> float:
    today = datetime.now(timezone.utc).date().isoformat()
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT COALESCE(SUM(cost_usd), 0) FROM calls WHERE created_at LIKE ?",
        (f"{today}%",),
    ).fetchone()
    conn.close()
    return row[0]


def get_costs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT substr(created_at, 1, 10) AS day,
               provider,
               model,
               COUNT(*) AS calls,
               SUM(input_tokens) AS input_tokens,
               SUM(output_tokens) AS output_tokens,
               ROUND(SUM(cost_usd), 8) AS cost_usd,
               CAST(AVG(CASE WHEN cached = 0 THEN latency_ms END) AS INTEGER) AS avg_latency_ms,
               SUM(fallback_count) AS fallbacks,
               SUM(cached) AS cache_hits
        FROM calls
        GROUP BY day, provider, model
        ORDER BY day DESC, cost_usd DESC
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]