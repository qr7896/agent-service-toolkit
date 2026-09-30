"""Fresh 20-task DEV identity using a direct HTTP client after TLS ambiguity."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
from pathlib import Path

import httpx
from langchain_openai import ChatOpenAI

from core.settings import settings
from evals import e1c_dev_v33 as runner
from evals.e1c_evidence_v22 import excerpts
from evals.e1c_live_runner import MANIFEST_SHA256, OUT, _save, _source

RUN_ID = "e1c-dev-v34-direct20-20260924"
RUN_DIR = OUT / RUN_ID
SKIPPED = ("sympy__sympy-13798", "sympy__sympy-17318", "sympy__sympy-18211")
runner.RUN_ID = RUN_ID
runner.RUN_DIR = RUN_DIR


def _rows() -> list[dict]:
    prior = json.loads((OUT / "e1c-dev-v33-localize23-20260924" / "state.json").read_text(encoding="utf-8"))
    if (prior["status"] != "network_ambiguous_stop" or len(prior["rows"]) != 3
            or tuple(row["instance_id"] for row in prior["rows"]) != SKIPPED):
        raise ValueError("v3.3 interrupted cohort changed")
    rows = runner._cohort()[3:]
    if len(rows) != 20 or any(row["instance_id"] in SKIPPED for row in rows):
        raise ValueError("remaining DEV cohort changed")
    return rows


def preflight() -> dict:
    rows = []
    for row in _rows():
        source = _source(row)
        admission = OUT / "admission_v2" / row["instance_id"]
        base = json.loads((admission / "base.json").read_text(encoding="utf-8"))
        gold = json.loads((admission / "gold.json").read_text(encoding="utf-8"))
        digest = subprocess.check_output(
            ["docker", "image", "inspect", base["image"], "--format", "{{index .RepoDigests 0}}"], text=True,
        ).strip()
        if not (base["phase_pass"] and gold["phase_pass"] and digest == base["image_digest"] == gold["image_digest"]):
            raise ValueError(f"admission changed: {row['instance_id']}")
        windows = excerpts(runner._statement(row["instance_id"]), source, max_files=6, max_chars=2200)
        if not windows:
            raise ValueError(f"no public source evidence: {row['instance_id']}")
        value = runner._payload(row, windows[:3], "", "")
        rows.append({"instance_id": row["instance_id"], "reserve": runner._reserve(value)})
    return {"run_id": RUN_ID, "manifest_sha256": MANIFEST_SHA256,
            "run_dir_absent": not RUN_DIR.exists(), "ready": len(rows) == 20 and not RUN_DIR.exists(),
            "task_count": len(rows), "skipped_v33_ambiguous_or_attempted": SKIPPED,
            "max_calls_per_task": runner.MAX_CALLS, "output_cap": runner.OUTPUT_CAP,
            "task_cap": runner.TASK_CAP, "total_cap": 20 * runner.TASK_CAP,
            "http_client": "httpx.AsyncClient(trust_env=False)", "rows": rows}


async def run() -> dict:
    gate = preflight()
    if not gate["ready"]:
        raise RuntimeError("v3.4 zero-call preflight failed")
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    _save(RUN_DIR / "identity.json", {**gate, "launcher_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                       "engine_sha256": hashlib.sha256(Path(runner.__file__).read_bytes()).hexdigest(),
                                       "model": "deepseek-flash", "sdk_retries": 0,
                                       "claim_boundary": "outcome-selected DEV; no ambiguous retry"})
    state = {"run_id": RUN_ID, "rows": []}
    ambiguous = 0
    async with httpx.AsyncClient(trust_env=False, timeout=60) as client:
        model = ChatOpenAI(model="deepseek-flash", temperature=0.5, streaming=False,
                           openai_api_base="https://api.deepseek.com",
                           openai_api_key=settings.DEEPSEEK_API_KEY, max_retries=0,
                           http_async_client=client)
        for row in _rows():
            try:
                outcome = await runner._task(row, model)
            except Exception as exc:
                state.update({"status": "interrupted_no_auto_retry", "interrupted_task": row["instance_id"],
                              "error": f"{type(exc).__name__}: {exc}"})
                _save(RUN_DIR / "state.json", state)
                raise
            state["rows"].append(outcome)
            _save(RUN_DIR / "state.json", state)
            print(json.dumps({"instance_id": outcome["instance_id"], "resolved": outcome["resolved"],
                              "status": outcome["status"], "calls": outcome["model_calls"],
                              "tokens": outcome["provider_tokens"]}), flush=True)
            ambiguous += outcome["status"] == "ambiguous_no_retry"
            if ambiguous >= 2:
                state.update({"status": "network_ambiguous_stop", "remaining_tasks_not_attempted": 20 - len(state["rows"])})
                _save(RUN_DIR / "state.json", state)
                return state
    state["status"] = "completed"
    _save(RUN_DIR / "state.json", state)
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run"))
    args = parser.parse_args()
    value = preflight() if args.command == "preflight" else asyncio.run(run())
    print(json.dumps(value if args.command == "preflight" else {
        "run_id": RUN_ID, "status": value["status"], "rows": len(value["rows"]),
        "new_resolved": sum(row["resolved"] for row in value["rows"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
