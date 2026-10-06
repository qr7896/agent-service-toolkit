"""Zero-provider DEV replay: separate controller execution metadata from generation."""

from __future__ import annotations

import argparse
import asyncio
import json
from types import SimpleNamespace

from langchain_core.messages import AIMessage

from evals import e1c_evaluation_2_executable_dev as study
from evals.e1c_evaluation_2_controller_manifest import parse_response
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_hybrid_oracle_replay import CacheOnlyModel

SOURCE = study.OUT
OUT = ROOT / ".codex/e1c/evaluation_2/controller-manifest-cache-dev-v3"
PROTOCOL = ROOT / "docs/research/E1C2_CONTROLLER_MANIFEST_CACHE_PROTOCOL_2026-10-06.md"
runtime = study.runtime
_preflight, _record = study.preflight, runtime.response_record
MISSES = []


async def invoke_cached(model, messages, config, *, role):
    iid = config["configurable"]["provider_task_id"]
    path = SOURCE / iid / role.rsplit("_", 1)[-1] / "response.json"
    if not path.exists():
        MISSES.append({"instance_id": iid, "role": role})
        return AIMessage(content='{"abstain_reason":"controller cache missing; no provider allowed"}',
                         response_metadata={"finish_reason": "stop", "cache_missing": True},
                         usage_metadata={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0})
    value = json.loads(path.read_bytes())
    return AIMessage(content=value["raw"], usage_metadata=value["usage"], response_metadata={
        "finish_reason": value["finish_reason"], "model_name": value["provider_model"], "cached_response_sha256": _sha(path)})


def record_cached(response):
    return {**_record(response), "cached_response_sha256": response.response_metadata.get("cached_response_sha256"),
            "controller_cache_missing": response.response_metadata.get("cache_missing", False),
            "usage_is_upstream_not_new": True, "new_provider_calls": 0}


def configure():
    study.OUT, study.preflight, study.parse_response = OUT, preflight, parse_response
    study.configure()
    runtime.RawJsonFlash, runtime.budgeted_ainvoke, runtime.response_record = CacheOnlyModel, invoke_cached, record_cached
    runtime.settings = SimpleNamespace(DEEPSEEK_API_KEY="cache-only-no-provider")


def preflight():
    configure()
    value = _preflight()
    configure()
    if value != json.loads((SOURCE / "freeze.json").read_bytes()):
        raise ValueError("source method/input changed; cannot interpret compatibility replay")
    return {**value, "schema": "e1c2-controller-manifest-cached-dev-v3", "provider_calls": 0, "max_provider_calls": 0,
            "generator_execution_manifest_required": False, "explicit_execution_manifest_required": False,
            "execution_owner": "controller_grammar", "generation_method_is_upstream_v2_not_new_v3": True,
            "source_freeze_sha256": _sha(SOURCE / "freeze.json"), "source_state_sha256": _sha(SOURCE / "state.json"),
            "source_ledger_sha256": _sha(SOURCE / "provider_calls.jsonl"), "protocol_sha256": _sha(PROTOCOL),
            "controller_modules": {name: _sha(ROOT / name) for name in (
                "evals/e1c_evaluation_2_controller_manifest.py", "evals/e1c_evaluation_2_controller_manifest_replay.py")},
            "cached_responses": {p.relative_to(SOURCE).as_posix(): _sha(p) for p in sorted(SOURCE.glob("*/*/response.json"))}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "gold"))
    args = parser.parse_args()
    configure()
    if args.command == "preflight":
        value = runtime.freeze()
    elif args.command == "run":
        try:
            value = asyncio.run(study.dev.run())
        finally:
            _save(OUT / "cache_status.json", {"missing_roles": MISSES, "provider_calls": 0,
                                            "controller_missing_markers_are_not_model_responses": True})
    else:
        value = runtime.grade()
    print(json.dumps({"provider_calls": 0, "result": value}))
