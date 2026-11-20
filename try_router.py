from app.providers.base import BaseProvider
from app.router import Router


class BrokenProvider(BaseProvider):
    name = "broken"

    def generate(self, prompt, model):
        raise ConnectionError("Simulated outage")


router = Router()

prompts = [
    "What is an API?",
    "Summarise the benefits of cloud computing.",
    "Debug this Python code: def add(a, b): return a - b",
]

for prompt in prompts:
    result = router.route(prompt)
    print(f"\n[{result.tier}] {prompt}")
    print(f"-> {result.response.provider}/{result.response.model}, "
          f"${result.cost_usd:.8f}, {result.latency_ms} ms")
    print(result.response.text[:150])

print("\n=== Simulating a Groq outage ===")
router.providers["groq"] = BrokenProvider()
result = router.route("What is an API?")
print(f"-> answered by {result.response.provider}/{result.response.model}")
print(f"failed attempts: {result.failed_attempts}")