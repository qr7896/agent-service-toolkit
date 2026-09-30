"""Single DEV canary showing the complete AlterField call omitted in v3.5."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

import httpx
from langchain_openai import ChatOpenAI

from core.settings import settings
from evals import e1c_dev_v33 as runner
from evals import e1c_dev_v37 as launcher
from evals.e1c_live_runner import OUT, _save

RUN_ID = "e1c-dev-v38-alterfield-window1-20260924"
RUN_DIR = OUT / RUN_ID
INSTANCE_ID = "django__django-11740"
SOURCE_PATH = "django/db/migrations/autodetector.py"
runner.RUN_ID = launcher.RUN_ID = RUN_ID
runner.RUN_DIR = launcher.RUN_DIR = RUN_DIR
runner.MAX_CALLS = 2
runner.TASK_CAP = 22_000
launcher.INSTANCE_ID = INSTANCE_ID


def _excerpts(_statement_text: str, workspace: Path, **_kwargs: object) -> list[dict]:
    lines = (workspace / SOURCE_PATH).read_text(encoding="utf-8").splitlines()
    anchors = ("if old_field_dec != new_field_dec:",
               "def _get_dependencies_for_foreign_key(", "def add_operation(")
    result = []
    for anchor in anchors:
        at = next(index for index, line in enumerate(lines) if anchor in line)
        start = max(0, at - (5 if anchor.startswith("if") else 2))
        end = min(len(lines), at + (37 if anchor.startswith("if") else 32))
        result.append({"path": SOURCE_PATH, "start_line": start + 1,
                       "text": "\n".join(lines[start:end])})
    if "field=field" not in result[0]["text"] or "dependencies" not in result[1]["text"]:
        raise ValueError("complete AlterField/dependency evidence not available")
    return result


runner.excerpts = _excerpts


def preflight() -> dict:
    return launcher.preflight()


async def run() -> dict:
    gate = preflight()
    if not gate["ready"]:
        raise RuntimeError("v3.8 zero-call preflight failed")
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    _save(RUN_DIR / "identity.json", {**gate,
                                      "launcher_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                      "engine_sha256": hashlib.sha256(Path(runner.__file__).read_bytes()).hexdigest(),
                                      "source_window": "complete original-base AlterField call",
                                      "model": "deepseek-flash", "sdk_retries": 0})
    state = {"run_id": RUN_ID, "rows": []}
    async with httpx.AsyncClient(trust_env=False, timeout=60) as client:
        model = ChatOpenAI(model="deepseek-flash", temperature=0.5, streaming=False,
                           openai_api_base="https://api.deepseek.com",
                           openai_api_key=settings.DEEPSEEK_API_KEY, max_retries=0,
                           http_async_client=client)
        try:
            outcome = await runner._task(launcher._row(), model)
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
