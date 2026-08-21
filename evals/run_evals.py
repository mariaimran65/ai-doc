"""AI-Doc evaluation harness — LLM-as-judge.

Runs the 12-example eval set against the live API, then scores each response
on three dimensions using Claude as a judge:

  accuracy     1-3   Is the answer factually correct given the context?
  completeness 1-3   Does the answer address all parts of the question?
  groundedness 1-3   Does the answer use provided data (tool results / chunks)
                     rather than fabricating from training knowledge?

Max score per example: 9. Full set (12 examples): max 108.

Usage
-----
  # Run against the live site
  python evals/run_evals.py --base-url https://aidoc.talent.techsupersonic.com

  # Run against local dev
  python evals/run_evals.py --base-url http://localhost:8000

  # Save results to a JSON file
  python evals/run_evals.py --output results.json

Environment variables required
-------------------------------
  ANTHROPIC_API_KEY   — for the judge LLM calls
  EVAL_JWT_TOKEN      — a valid JWT access_token for the AI-Doc API
                        (generate one via docker exec or a test fixture)

LangSmith integration
---------------------
  Set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY to record every judge
  call as a trace in your ai-doc LangSmith project.
"""

import argparse
import json
import os
import sys
import time
from typing import Any

import httpx
from anthropic import Anthropic

EVAL_SET_PATH = os.path.join(os.path.dirname(__file__), "eval_set.json")

JUDGE_SYSTEM = """You are a strict evaluator assessing AI assistant responses.
Score the response on three dimensions, each from 1 to 3:

accuracy:     1 = factually wrong or hallucinated
              2 = mostly correct, minor errors or omissions
              3 = fully correct with no hallucinations

completeness: 1 = misses most of what was asked
              2 = addresses the main point but misses important parts
              3 = fully addresses every part of the question

groundedness: 1 = relies on training knowledge, ignores provided context/tools
              2 = uses some provided context but also adds ungrounded claims
              3 = answer is fully derived from provided tool results or document chunks

Respond with a JSON object only — no markdown, no explanation:
{"accuracy": <1-3>, "completeness": <1-3>, "groundedness": <1-3>, "rationale": "<one sentence>"}
"""


def load_eval_set() -> list[dict]:
    with open(EVAL_SET_PATH) as f:
        data = json.load(f)
    return data["examples"]


def call_chat_endpoint(base_url: str, token: str, question: str) -> str:
    """POST to /chat/ and collect the SSE stream into a single string."""
    url = f"{base_url.rstrip('/')}/chat/"
    payload = {"messages": [{"role": "user", "content": question}]}
    cookies = {"access_token": token}

    chunks: list[str] = []
    with httpx.Client(timeout=60) as client:
        with client.stream("POST", url, json=payload, cookies=cookies) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line.startswith("data:") and "[DONE]" not in line:
                    try:
                        data = json.loads(line[5:].strip())
                        if "token" in data:
                            chunks.append(data["token"])
                        elif "error" in data:
                            return f"[ERROR] {data['error']}"
                    except json.JSONDecodeError:
                        pass
    return "".join(chunks)


def call_agents_endpoint(base_url: str, token: str, task: str) -> str:
    """POST to /agents/run and collect the SSE stream."""
    url = f"{base_url.rstrip('/')}/agents/run"
    payload = {"task": task}
    cookies = {"access_token": token}

    parts: list[str] = []
    with httpx.Client(timeout=120) as client:
        with client.stream("POST", url, json=payload, cookies=cookies) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line.startswith("data:") and "[DONE]" not in line:
                    try:
                        data = json.loads(line[5:].strip())
                        if "output" in data:
                            parts.append(data["output"])
                        elif "error" in data:
                            return f"[ERROR] {data['error']}"
                    except json.JSONDecodeError:
                        pass
    return "\n".join(parts)


def call_rag_endpoint(base_url: str, token: str, question: str) -> str:
    """POST to /knowledge/ask and collect the SSE stream."""
    url = f"{base_url.rstrip('/')}/knowledge/ask"
    payload = {"question": question}
    cookies = {"access_token": token}

    chunks: list[str] = []
    with httpx.Client(timeout=60) as client:
        with client.stream("POST", url, json=payload, cookies=cookies) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line.startswith("data:") and "[DONE]" not in line:
                    try:
                        data = json.loads(line[5:].strip())
                        if "token" in data:
                            chunks.append(data["token"])
                        elif "error" in data:
                            return f"[ERROR] {data['error']}"
                    except json.JSONDecodeError:
                        pass
    return "".join(chunks)


def judge(client: Anthropic, question: str, reference: str, response: str) -> dict:
    """Call Claude as a judge and return scores dict."""
    user_msg = (
        f"Question: {question}\n\n"
        f"Reference answer (what a good response should cover):\n{reference}\n\n"
        f"Actual response:\n{response}"
    )
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = msg.content[0].text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"accuracy": 1, "completeness": 1, "groundedness": 1, "rationale": f"judge parse error: {raw}"}


def run_evals(base_url: str, token: str) -> list[dict[str, Any]]:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    examples = load_eval_set()
    results = []

    for ex in examples:
        cat = ex["category"]
        print(f"  [{cat}] {ex['id']} — {ex['input'][:60]}...")

        t0 = time.time()
        if cat == "chat":
            response = call_chat_endpoint(base_url, token, ex["input"])
        elif cat == "agents":
            response = call_agents_endpoint(base_url, token, ex["input"])
        else:
            response = call_rag_endpoint(base_url, token, ex["input"])
        latency = round(time.time() - t0, 2)

        scores = judge(client, ex["input"], ex["reference"], response)
        total = scores.get("accuracy", 1) + scores.get("completeness", 1) + scores.get("groundedness", 1)

        result = {
            "id": ex["id"],
            "category": cat,
            "input": ex["input"],
            "response": response[:500],
            "latency_s": latency,
            "accuracy": scores.get("accuracy", 1),
            "completeness": scores.get("completeness", 1),
            "groundedness": scores.get("groundedness", 1),
            "total": total,
            "rationale": scores.get("rationale", ""),
        }
        results.append(result)
        print(f"    score {total}/9  ({scores.get('rationale', '')})")

    return results


def summarise(results: list[dict]) -> None:
    total_score = sum(r["total"] for r in results)
    max_score = len(results) * 9

    by_cat: dict[str, list] = {}
    for r in results:
        by_cat.setdefault(r["category"], []).append(r["total"])

    print("\n" + "=" * 60)
    print(f"  TOTAL SCORE: {total_score} / {max_score}")
    print("=" * 60)
    for cat, scores in by_cat.items():
        cat_total = sum(scores)
        cat_max = len(scores) * 9
        print(f"  {cat:<10} {cat_total:>3} / {cat_max}")
    print("=" * 60)

    avg_latency = sum(r["latency_s"] for r in results) / len(results)
    print(f"  avg latency: {avg_latency:.1f}s per call")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AI-Doc eval harness")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--output", help="Write full results to this JSON file")
    args = parser.parse_args()

    token = os.environ.get("EVAL_JWT_TOKEN")
    if not token:
        print("Error: EVAL_JWT_TOKEN environment variable not set.", file=sys.stderr)
        sys.exit(1)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    print(f"\nRunning evals against {args.base_url} ...\n")
    results = run_evals(args.base_url, token)
    summarise(results)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Full results written to {args.output}")


if __name__ == "__main__":
    main()
