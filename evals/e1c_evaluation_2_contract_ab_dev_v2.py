"""Second matched DEV trial: production coverage and raw, metered JSON responses."""

from __future__ import annotations

import argparse
import asyncio
import json

from evals import e1c_evaluation_2_contract_ab_dev as original
from evals import e1c_evaluation_2_production_coverage as coverage
from evals.e1c_evaluation_2_dev_pilot import ROOT, _sha
from evals.e1c_evaluation_2_raw_json import RawJsonFlash

OUT = ROOT / ".codex/e1c/evaluation_2/contract-ab-dev-v2"
PROTOCOL = ROOT / "docs/research/E1C2_CONTRACT_AB_DEV_V2_PROTOCOL_2026-10-05.md"
_messages = original.messages
_preflight = original.preflight
_standard_model = original.ChatOpenAI


def prepare():
    rows = coverage.prepare()["rows"]
    return [(row["instance_id"], json.loads(path.read_bytes()), path) for row in rows
            for path in [coverage.OUT / "inputs" / f"{row['instance_id']}.json"]]


def messages(frozen, arm):
    result = _messages(frozen, arm)
    if arm == "B":
        result[0].content += (
            " If issue code omits variable construction but explicitly states the input type and behavior, "
            "construct the smallest deterministic valid fixture of that type from production signatures. "
            "Do not abstain merely because X/y values are omitted. Baseline control may change only the "
            "failure-triggering condition. Copy quote spans exactly without paraphrasing. "
            "For value_relation use one explicit comparison; express boolean predicates as == True or == False "
            "rather than a bare predicate or unary-not assert."
        )
    return result


def configure(arm):
    original.OUT, original.PROTOCOL = OUT, PROTOCOL
    original.prepare, original.messages = prepare, messages
    original.ChatOpenAI = RawJsonFlash if arm == "B" else _standard_model
    original.preflight = preflight


def preflight(arm):
    configure(arm)
    value = _preflight(arm)
    value.update({"schema": "e1c2-contract-ab-dev-arm-freeze-v2", "run_id": f"e1c2-contract-ab-dev-v2-{arm.lower()}",
                  "v2_modules": {name: _sha(ROOT / name) for name in (
                      "evals/e1c_evaluation_2_contract_ab_dev_v2.py", "evals/e1c_evaluation_2_raw_json.py",
                      "evals/e1c_evaluation_2_production_coverage.py")}})
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "gold"))
    parser.add_argument("--arm", choices=("A", "B"), default="B")
    args = parser.parse_args()
    configure(args.arm)
    if args.command == "preflight":
        frozen = original.freeze(args.arm)
        value = {key: frozen[key] for key in ("arm", "model", "max_provider_calls", "total_reserve", "batch_token_cap")}
    elif args.command == "run":
        value = asyncio.run(original.run(args.arm))
    else:
        value = original.grade(args.arm)
    print(json.dumps(value, ensure_ascii=False))
