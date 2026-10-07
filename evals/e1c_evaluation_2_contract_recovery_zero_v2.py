"""New zero-provider identity: same cached first probes plus source-format control."""

from __future__ import annotations

import argparse
import json

from evals import e1c_evaluation_2_contract_recovery_zero as base
from evals.e1c_evaluation_2_contract_recovery import compile_contract as original_compile
from evals.e1c_evaluation_2_dev_pilot import ROOT, _sha
from evals.e1c_evaluation_2_source_format_control import derive_format_control

OUT = ROOT / ".codex/e1c/evaluation_2/contract-recovery-zero-dev-v2"
PROTOCOL = ROOT / "docs/research/E1C2_CONTRACT_RECOVERY_ZERO_DEV_V2_2026-10-07.md"
_preflight = base.preflight


def compile_contract(payload, frozen, workspace):
    canonical, proof = original_compile(payload, frozen, workspace)
    changed, format_proof = derive_format_control(canonical, frozen, workspace)
    return changed, {**proof, "source_format_control": format_proof}


def configure():
    base.OUT, base.PROTOCOL, base.compile_contract, base.preflight = OUT, PROTOCOL, compile_contract, preflight


def preflight():
    configure()
    value = _preflight()
    return {**value, "schema": "e1c2-contract-recovery-zero-freeze-v2", "control_method_changed": True,
            "method_sha256": {**value["method_sha256"], **{n: _sha(ROOT / n) for n in (
                "evals/e1c_evaluation_2_source_format_control.py", "evals/e1c_evaluation_2_contract_recovery_zero_v2.py")}}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("zero", "gold"))
    args = parser.parse_args()
    configure()
    print(json.dumps(base.zero() if args.command == "zero" else base.grade(), ensure_ascii=False))
