"""Unattempted v3.5 HEAD-request DEV task under a fresh one-task identity."""

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
from evals import e1c_dev_v35 as localization
from evals.e1c_live_runner import MANIFEST_SHA256, OUT, _manifest, _save, _source

RUN_ID = "e1c-dev-v37-head-canary1-20260924"
RUN_DIR = OUT / RUN_ID
INSTANCE_ID = "django__django-16502"
runner.RUN_ID = RUN_ID
runner.RUN_DIR = RUN_DIR
runner.MAX_CALLS = 2
runner.OUTPUT_CAP = 1800
runner.TASK_CAP = 20_000


def _row() -> dict:
    return next(row for row in _manifest()["tasks"] if row["instance_id"] == INSTANCE_ID)


def preflight() -> dict:
    row = _row()
    source = _source(row)
    windows = runner.excerpts(runner._statement(INSTANCE_ID), source)
    reserve = runner._reserve(runner._payload(row, windows, "", ""))
    admission = OUT / "admission_v2" / INSTANCE_ID
    base = json.loads((admission / "base.json").read_text(encoding="utf-8"))
    gold = json.loads((admission / "gold.json").read_text(encoding="utf-8"))
    digest = subprocess.check_output(
        ["docker", "image", "inspect", base["image"], "--format", "{{index .RepoDigests 0}}"], text=True,
    ).strip()
    return {"run_id": RUN_ID, "manifest_sha256": MANIFEST_SHA256,
            "run_dir_absent": not RUN_DIR.exists(),
            "ready": not RUN_DIR.exists() and reserve * 2 <= runner.TASK_CAP
            and base["phase_pass"] and gold["phase_pass"]
            and digest == base["image_digest"] == gold["image_digest"],
            "instance_id": INSTANCE_ID, "reserve": reserve, "max_calls": 2,
            "output_cap": runner.OUTPUT_CAP, "task_cap": runner.TASK_CAP,
            "claim_boundary": "public human-localized DEV; not independent efficacy"}


async def run() -> dict:
    gate = preflight()
    if not gate["ready"]:
        raise RuntimeError("v3.7 zero-call preflight failed")
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    _save(RUN_DIR / "identity.json", {**gate,
                                      "launcher_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                      "engine_sha256": hashlib.sha256(Path(runner.__file__).read_bytes()).hexdigest(),
                                      "localization_sha256": hashlib.sha256(Path(localization.__file__).read_bytes()).hexdigest(),
                                      "model": "deepseek-flash", "sdk_retries": 0})
    state = {"run_id": RUN_ID, "rows": []}
    async with httpx.AsyncClient(trust_env=False, timeout=60) as client:
        model = ChatOpenAI(model="deepseek-flash", temperature=0.5, streaming=False,
                           openai_api_base="https://api.deepseek.com",
                           openai_api_key=settings.DEEPSEEK_API_KEY, max_retries=0,
                           http_async_client=client)
        try:
            outcome = await runner._task(_row(), model)
        except Exception as exc:
            state.update({"status": "interrupted_no_auto_retry", "error": f"{type(exc).__name__}: {exc}"})
            _save(RUN_DIR / "state.json", state)
            raise
    state["rows"].append(outcome)
    state["status"] = "completed" if outcome["status"] == "completed" else outcome["status"]
    _save(RUN_DIR / "state.json", state)
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run"))
    args = parser.parse_args()
    value = preflight() if args.command == "preflight" else asyncio.run(run())
    print(json.dumps(value if args.command == "preflight" else {
        "run_id": RUN_ID, "status": value["status"], "resolved": value["rows"][0]["resolved"],
        "tokens": value["rows"][0]["provider_tokens"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
