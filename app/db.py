import sqlite3
from datetime import datetime, timezone

from app.router import RouteResult

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
            fallback_count INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def log_call(result: RouteResult):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO calls (created_at, tier, provider, model, input_tokens,
                           output_tokens, cost_usd, latency_ms, fallback_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            result.tier,
            result.response.provider,
            result.response.model,
            result.response.input_tokens,
            result.response.output_tokens,
            result.cost_usd,
            result.latency_ms,
            len(result.failed_attempts),
        ),
    )
    conn.commit()
    conn.close()


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
               CAST(AVG(latency_ms) AS INTEGER) AS avg_latency_ms,
               SUM(fallback_count) AS fallbacks
        FROM calls
        GROUP BY day, provider, model
        ORDER BY day DESC, cost_usd DESC
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]