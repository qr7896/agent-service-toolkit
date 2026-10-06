"""Zero-provider replay of preserved faithful DEV outputs after Docker recovery."""

from __future__ import annotations

import argparse
import asyncio
import json
from types import SimpleNamespace

from langchain_core.messages import AIMessage

from evals import e1c_evaluation_2_faithful_dev as faithful
from evals.e1c_evaluation_2_container_health import require_engine, require_valid_execution_files
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_hybrid_oracle_replay import CacheOnlyModel

SOURCE = faithful.OUT
OUT = ROOT / ".codex/e1c/evaluation_2/faithful-input-dev-v1-infra-replay-v1"
PROTOCOL = ROOT / "docs/research/E1C2_FAITHFUL_INFRA_REPLAY_2026-10-06.md"
runtime = faithful.base.study.runtime
_preflight, _record, _execute = faithful.preflight, runtime.response_record, faithful.base.study.execute_role
MISSES = []


def guarded_execute(role, payload, frozen, workspace, image, root, environment):
    require_engine((image,))
    value = _execute(role, payload, frozen, workspace, image, root, environment)
    require_valid_execution_files(root)
    return value


async def invoke_cached(model, messages, config, *, role):
    iid = config["configurable"]["provider_task_id"]
    path = SOURCE / iid / role.rsplit("_", 1)[-1] / "response.json"
    if not path.is_file():
        MISSES.append({"instance_id": iid, "role": role, "status": "upstream_response_not_collected"})
        return AIMessage(content=json.dumps({"abstain_reason": "controller cache unavailable; no model request allowed"}),
                         response_metadata={"finish_reason": "stop", "cache_missing": True},
                         usage_metadata={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0})
    value = json.loads(path.read_bytes())
    return AIMessage(content=value["raw"], usage_metadata=value["usage"], response_metadata={
        "finish_reason": value["finish_reason"], "model_name": value["provider_model"], "cached_response_sha256": _sha(path)})


def cached_record(response):
    return {**_record(response), "cached_response_sha256": response.response_metadata.get("cached_response_sha256"),
            "controller_cache_missing": response.response_metadata.get("cache_missing", False),
            "usage_is_upstream_not_new": True, "new_provider_calls": 0}


def configure():
    faithful.OUT = OUT
    faithful.preflight = preflight
    faithful.configure()
    runtime.preflight, runtime.execute_role = preflight, guarded_execute
    runtime.RawJsonFlash, runtime.budgeted_ainvoke, runtime.response_record = CacheOnlyModel, invoke_cached, cached_record
    runtime.settings = SimpleNamespace(DEEPSEEK_API_KEY="cache-only-no-provider")


def preflight():
    source = json.loads((SOURCE / "freeze.json").read_bytes())
    require_engine(tuple(row["image_id"] for row in source["tasks"]))
    configure()
    value = _preflight()
    runtime.preflight, runtime.execute_role = preflight, guarded_execute
    if value != source:
        raise ValueError("source model method/input bytes changed; no replay permitted")
    return {**value, "schema": "e1c2-faithful-zero-provider-infra-replay-v1", "provider_calls": 0,
            "max_provider_calls": 0, "upstream_provider_calls_retried": False,
            "source_freeze_sha256": _sha(SOURCE / "freeze.json"), "source_state_sha256": _sha(SOURCE / "state.json"),
            "source_ledger_sha256": _sha(SOURCE / "provider_calls.jsonl"), "protocol_sha256": _sha(PROTOCOL),
            "infra_modules": {name: _sha(ROOT / name) for name in (
                "evals/e1c_evaluation_2_faithful_infra_replay.py", "evals/e1c_evaluation_2_container_health.py")},
            "cached_responses": {path.relative_to(SOURCE).as_posix(): _sha(path) for path in sorted(SOURCE.glob("*/*/response.json"))}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "gold"))
    args = parser.parse_args()
    configure()
    if args.command == "preflight":
        result = runtime.freeze()
    elif args.command == "run":
        try:
            result = asyncio.run(faithful.base.study.dev.run())
        finally:
            _save(OUT / "cache_status.json", {"missing_roles": MISSES, "provider_calls": 0,
                                             "controller_generated_abstentions_are_not_model_outputs": True})
    else:
        require_engine()
        result = runtime.grade()
    print(json.dumps({"provider_calls": 0, "result": result}, ensure_ascii=False))
