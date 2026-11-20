import hashlib
import json

import redis

CACHE_TTL_SECONDS = 24 * 60 * 60


class ResponseCache:
    def __init__(self, url: str):
        self.client = redis.Redis.from_url(url, decode_responses=True, socket_timeout=1)

    @staticmethod
    def make_key(prompt: str) -> str:
        digest = hashlib.sha256(prompt.strip().encode("utf-8")).hexdigest()
        return f"llm-cache:{digest}"

    def get(self, prompt: str) -> dict | None:
        try:
            value = self.client.get(self.make_key(prompt))
        except redis.RedisError:
            return None
        return json.loads(value) if value else None

    def set(self, prompt: str, data: dict) -> None:
        try:
            self.client.set(self.make_key(prompt), json.dumps(data), ex=CACHE_TTL_SECONDS)
        except redis.RedisError:
            pass