import csv
import json
import re
import sys
import time
from pathlib import Path

from app.config import MODEL_PRICES, TIER_MODELS
from app.pricing import calculate_cost
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider
from app.router import classify

EVAL_DIR = Path(__file__).parent
RESULTS_PATH = EVAL_DIR / "results.csv"
INSTRUCTION = "\n\nGive only the final answer, with no explanation."
PAUSE_SECONDS = 2
TIERS = ("simple", "medium", "hard")
MAX_ATTEMPTS = 3
RETRY_WAIT_SECONDS = 15


class EmptyAnswer(Exception):
    pass


def is_correct(answer: str, must_contain: list[str]) -> bool:
    text = answer.lower()
    return all(re.search(rf"\b{re.escape(term.lower())}\b", text) for term in must_contain)


def call_with_retry(provider, prompt: str, model: str):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = provider.generate(prompt, model)
            if not (response.text or "").strip():
                raise EmptyAnswer("model returned an empty answer")
            return response
        except Exception as e:
            if attempt == MAX_ATTEMPTS:
                raise
            wait = RETRY_WAIT_SECONDS * attempt
            print(f"    retry {attempt} after {type(e).__name__}: {str(e)[:80]} (waiting {wait}s)")
            time.sleep(wait)


def run_model(provider, model: str, items: list[dict]) -> list[dict]:
    rows = []
    for item in items:
        start = time.perf_counter()
        try:
            response = call_with_retry(provider, item["question"] + INSTRUCTION, model)
            answer = response.text.strip()
            cost = calculate_cost(model, response.input_tokens, response.output_tokens)
            error = ""
        except Exception as e:
            answer, cost, error = "", 0.0, f"{type(e).__name__}: {e}"
        latency_ms = int((time.perf_counter() - start) * 1000)
        correct = is_correct(answer, item["must_contain"])

        rows.append({
            "id": item["id"],
            "tier": item["tier"],
            "model": model,
            "question": item["question"],
            "answer": answer,
            "correct": correct,
            "cost_usd": cost,
            "latency_ms": latency_ms,
            "error": error,
        })
        status = "ERROR" if error else ("PASS" if correct else "FAIL")
        print(f"  {status} [{item['tier']}] #{item['id']} {(error or answer)[:70]!r}")
        time.sleep(PAUSE_SECONDS)
    return rows


def summarise(rows: list[dict]) -> dict:
    answered = [r for r in rows if not r["error"]]
    return {
        "accuracy": sum(r["correct"] for r in answered) / len(answered) * 100 if answered else 0.0,
        "errors": len(rows) - len(answered),
        "total_cost": sum(r["cost_usd"] for r in rows),
        "avg_latency": sum(r["latency_ms"] for r in answered) / len(answered) if answered else 0.0,
    }


def save_csv(rows: list[dict]) -> None:
    with open(RESULTS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def load_csv() -> list[dict]:
    if not RESULTS_PATH.exists():
        return []
    with open(RESULTS_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["id"] = int(r["id"])
        r["correct"] = r["correct"] == "True"
        r["cost_usd"] = float(r["cost_usd"])
        r["latency_ms"] = int(r["latency_ms"])
    return rows


def print_model_table(rows: list[dict]) -> None:
    print("\n## Accuracy and cost per model\n")
    print("| Model | Overall | Simple | Medium | Hard | Errors | Total cost (20 Qs) | Avg latency |")
    print("|---|---|---|---|---|---|---|---|")
    for model in MODEL_PRICES:
        model_rows = [r for r in rows if r["model"] == model]
        if not model_rows:
            continue
        overall = summarise(model_rows)
        tiers = [summarise([r for r in model_rows if r["tier"] == t])["accuracy"] for t in TIERS]
        print(
            f"| {model} | {overall['accuracy']:.0f}% | {tiers[0]:.0f}% | {tiers[1]:.0f}% | {tiers[2]:.0f}% "
            f"| {overall['errors']} | ${overall['total_cost']:.6f} | {overall['avg_latency']:.0f} ms |"
        )


def print_router_comparison(rows: list[dict], items: list[dict]) -> None:
    lookup = {(r["model"], r["id"]): r for r in rows}
    routed = [lookup[(TIER_MODELS[classify(item["question"])][0], item["id"])] for item in items]

    print("\n## Router vs. sending everything to one model\n")
    print("| Strategy | Accuracy | Errors | Total cost (20 Qs) |")
    print("|---|---|---|---|")
    result = summarise(routed)
    print(f"| **Router** | {result['accuracy']:.0f}% | {result['errors']} | ${result['total_cost']:.6f} |")
    for model in MODEL_PRICES:
        result = summarise([r for r in rows if r["model"] == model])
        print(f"| Always {model} | {result['accuracy']:.0f}% | {result['errors']} | ${result['total_cost']:.6f} |")


def print_classifier_report(items: list[dict]) -> None:
    mismatches = [(item, classify(item["question"])) for item in items
                  if classify(item["question"]) != item["tier"]]
    matched = len(items) - len(mismatches)
    print(f"\n## Classifier: agreed with the human label on {matched}/{len(items)} questions\n")
    for item, predicted in mismatches:
        print(f"- labelled {item['tier']}, classified {predicted}: {item['question'][:70]}")


def print_report(rows: list[dict], items: list[dict]) -> None:
    print_model_table(rows)
    missing = [m for m in MODEL_PRICES if not any(r["model"] == m for r in rows)]
    if missing:
        print(f"\nRouter comparison skipped: no results yet for {missing}")
    else:
        print_router_comparison(rows, items)
    print_classifier_report(items)


def main() -> None:
    items = json.loads((EVAL_DIR / "dataset.json").read_text(encoding="utf-8"))
    args = sys.argv[1:]

    if args == ["report"]:
        print_report(load_csv(), items)
        return

    selected = args or list(MODEL_PRICES)
    unknown = [m for m in selected if m not in MODEL_PRICES]
    if unknown:
        raise SystemExit(f"Unknown model(s): {unknown}. Choose from: {list(MODEL_PRICES)}")

    all_rows = [r for r in load_csv() if r["model"] not in selected] if args else []
    providers = {"groq": GroqProvider(), "gemini": GeminiProvider()}

    for model in selected:
        print(f"\n=== {model} ===")
        all_rows += run_model(providers[MODEL_PRICES[model]["provider"]], model, items)
        save_csv(all_rows)

    print_report(all_rows, items)


if __name__ == "__main__":
    main()