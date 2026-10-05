"""Hybrid controller v2: fallback cannot add an unstated value oracle."""

from __future__ import annotations

import argparse
import asyncio
import json

from evals import e1c_evaluation_2_hybrid_dev as runtime
from evals.e1c_evaluation_2_contract_method import parse_response
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_fallback_oracle import compile_fallback

OUT = ROOT / ".codex/e1c/evaluation_2/hybrid-dev-v2"
PROTOCOL = ROOT / "docs/research/E1C2_HYBRID_CONTROLLER_V2_METHOD_2026-10-05.md"
_execute = runtime.execute_role
_preflight = runtime.preflight


def execute_role(role, payload, frozen, workspace, image, root, environment):
    if role == "A":
        primary_path = root.parent / "B" / "response.json"
        if primary_path.is_file():
            try:
                primary = parse_response(json.loads(primary_path.read_bytes())["raw"], "B")
            except ValueError:
                primary = {"status": "invalid_contract"}
            if primary["status"] == "candidate":
                source, proof = compile_fallback(payload["source"], primary["payload"], frozen)
                _save(root / "oracle_compilation.json", proof)
                payload = {"source": source}
    return _execute(role, payload, frozen, workspace, image, root, environment)


def configure():
    runtime.OUT, runtime.PROTOCOL = OUT, PROTOCOL
    runtime.execute_role, runtime.preflight = execute_role, preflight


def preflight():
    configure()
    value = _preflight()
    value.update({"schema": "e1c2-source-contract-hybrid-freeze-v2", "v2_modules": {
        name: _sha(ROOT / name) for name in ("evals/e1c_evaluation_2_hybrid_controller_v2.py", "evals/e1c_evaluation_2_fallback_oracle.py")}})
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "gold"))
    args = parser.parse_args()
    configure()
    result = runtime.freeze() if args.command == "preflight" else asyncio.run(runtime.run()) if args.command == "run" else runtime.grade()
    print(json.dumps(result, ensure_ascii=False))
