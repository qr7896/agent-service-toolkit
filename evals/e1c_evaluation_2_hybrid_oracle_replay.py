"""Replay the complete hybrid pilot with the oracle compiler, with no provider calls."""

from __future__ import annotations

import argparse
import asyncio
import json
from types import SimpleNamespace

from langchain_core.messages import AIMessage

from evals import e1c_evaluation_2_hybrid_controller_v2 as controller
from evals.e1c_evaluation_2_dev_pilot import ROOT, _sha

runtime = controller.runtime
SOURCE = ROOT / ".codex/e1c/evaluation_2/hybrid-dev-v1"
OUT = ROOT / ".codex/e1c/evaluation_2/hybrid-oracle-replay-dev-v1"
_record = runtime.response_record


def preflight():
    value = json.loads((SOURCE / "freeze.json").read_bytes())
    if any(_sha(ROOT / name) != digest for name, digest in value["modules"].items()):
        raise ValueError("source hybrid method changed")
    state = json.loads((SOURCE / "state.json").read_bytes())
    if state["status"] != "completed" or len(state["rows"]) != 9:
        raise ValueError("complete source hybrid pilot required")
    actual = runtime.inputs()
    if [row[0] for row in actual] != [row["instance_id"] for row in value["tasks"]] or any(
        _sha(path) != row["input_sha256"] or image != row["image_id"]
        for row, (_, _, path, _, image) in zip(value["tasks"], actual, strict=True)
    ):
        raise ValueError("source hybrid inputs/images changed")
    value.update({"schema": "e1c2-hybrid-oracle-cached-replay-v1", "provider_calls": 0, "max_provider_calls": 0,
                  "upstream_freeze_sha256": _sha(SOURCE / "freeze.json"), "upstream_state_sha256": _sha(SOURCE / "state.json"),
                  "cached_responses": {p.relative_to(SOURCE).as_posix(): _sha(p) for p in sorted(SOURCE.glob("*/*/response.json"))},
                  "compiler_modules": {name: _sha(ROOT / name) for name in (
                      "evals/e1c_evaluation_2_hybrid_oracle_replay.py", "evals/e1c_evaluation_2_hybrid_controller_v2.py",
                      "evals/e1c_evaluation_2_fallback_oracle.py")}})
    return value


class CacheOnlyModel:
    def __init__(self, **kwargs):
        pass

    def bind(self, **kwargs):
        return self


async def invoke_cached(model, messages, config, *, role):
    path = SOURCE / config["configurable"]["provider_task_id"] / role.rsplit("_", 1)[-1] / "response.json"
    if not path.is_file():
        raise ValueError("fallback output was not collected in source pilot; no model call in replay")
    data = json.loads(path.read_bytes())
    return AIMessage(content=data["raw"], usage_metadata=data["usage"], response_metadata={
        "finish_reason": data["finish_reason"], "model_name": data["provider_model"], "cached_response_sha256": _sha(path),
    })


def cached_record(response):
    return {**_record(response), "cached_response_sha256": response.response_metadata["cached_response_sha256"],
            "usage_is_upstream_not_new": True, "new_provider_calls": 0}


def configure():
    controller.OUT = OUT
    controller.configure()
    runtime.preflight = preflight
    runtime.RawJsonFlash = CacheOnlyModel
    runtime.settings = SimpleNamespace(DEEPSEEK_API_KEY="cache-only-no-provider")
    runtime.budgeted_ainvoke = invoke_cached
    runtime.response_record = cached_record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "gold"))
    args = parser.parse_args()
    configure()
    result = runtime.freeze() if args.command == "preflight" else asyncio.run(runtime.run()) if args.command == "run" else runtime.grade()
    print(json.dumps({"provider_calls": 0, "result": result}))
