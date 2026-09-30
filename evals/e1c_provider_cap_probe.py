"""One-call live probe of the DeepSeek thinking output cap; no task grading."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from langchain_core.messages import HumanMessage

from agents.model_budget import budgeted_ainvoke
from evals.e1c_live_runner import OUT, _model, _save

RUN_ID = "e1c-dev-v25-cap-probe-20260924"
RUN_DIR = OUT / RUN_ID
LEDGER = RUN_DIR / "provider_calls.jsonl"
PROMPT = "Output the digit 7 exactly 10000 times. No other text."


def preflight() -> dict:
    return {
        "run_id": RUN_ID,
        "run_dir_absent": not RUN_DIR.exists(),
        "model": "deepseek-flash",
        "max_calls": 1,
        "max_output_tokens": 512,
        "total_token_ceiling": 2000,
        "thinking": "enabled, low",
        "task_grade": "none",
    }


async def run() -> dict:
    if RUN_DIR.exists():
        raise RuntimeError("probe identity already used; never retry or overwrite")
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    _save(RUN_DIR / "identity.json", {
        **preflight(),
        "run_dir_absent": True,
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(),
        "claim_boundary": "provider-cap verification only; not a repair outcome",
    })
    try:
        response = await budgeted_ainvoke(
            _model().bind(reasoning_effort="low", extra_body={"thinking": {"type": "enabled"}}),
            [HumanMessage(content=PROMPT)],
            {"configurable": {
                "provider_ledger_path": str(LEDGER),
                "provider_run_id": RUN_ID,
                "provider_task_id": "cap-probe",
                "provider_total_token_ceiling": 2000,
                "provider_task_token_ceiling": 2000,
                "provider_max_calls_per_task": 1,
                "provider_max_output_tokens": 512,
                "provider_prompt_reserve_multiplier": 1.2,
            }},
            role="compact_editor",
        )
    except Exception as exc:
        result = {"status": "stopped", "error": f"{type(exc).__name__}: {exc}"}
        _save(RUN_DIR / "result.json", result)
        raise
    usage = response.usage_metadata or {}
    result = {
        "status": "completed",
        "usage": usage,
        "output_within_cap": int(usage.get("output_tokens") or 0) <= 512,
        "response_sha256": hashlib.sha256(str(response.content).encode()).hexdigest(),
    }
    _save(RUN_DIR / "result.json", result)
    if not result["output_within_cap"]:
        raise RuntimeError("live provider exceeded output cap; stop paid iteration")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run"))
    args = parser.parse_args()
    result = preflight() if args.command == "preflight" else asyncio.run(run())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
