"""Flash DEV contrast: distinguish issue-value oracles from no-exception oracles."""

from __future__ import annotations

import hashlib
from pathlib import Path

from evals import e1c_evaluation_2_unified_dev_v1 as base
from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_dev_pilot import _sha
from evals.e1c_evaluation_2_probe import input_json
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

base.RUN_ID = "e1c2-unified-dev-v4-flash"
base.OUT = ROOT / ".codex/e1c/evaluation_2" / base.RUN_ID
base.FREEZE = base.OUT / "freeze.json"
base.LEDGER = base.OUT / "provider_calls.jsonl"
base.MODEL = "deepseek-flash"
base.MAX_OUTPUT_TOKENS = 2600
base.TASK_TOKEN_CAP = 14_000
base.BATCH_TOKEN_CAP = 90_000


def prompt(frozen: dict) -> str:
    context = input_json({"issue": frozen["issue"], "windows": frozen["windows"]})
    if len(context) > 24_000:
        raise ValueError("issue-only context too large")
    value = (
        "Using only this public issue and exact-base production-source windows, write one standalone Python "
        "probe for the concrete behavior stated in the issue. If it is a discussion or RFC without a "
        "specific observable expectation, abstain. Preserve any public example's input type, values, "
        "setup, and API call; construct only missing setup required by the shown production signatures. "
        "Use exactly one assert. If the issue states an expected return value, assert only that stated "
        "value. If the issue instead says a real API call should succeed but currently raises, do not "
        "invent a return-value or internal-attribute expectation: set a local completion flag after the "
        "real API call and assert the flag. This observes only whether the call raised; do not use "
        "assert True. Do not fabricate failures, mocks, warnings, results, dummy objects with missing "
        "members, or extra assertions. If there is no sound issue-grounded oracle, abstain. Do not use "
        "hidden patches, tests, task IDs, grader artifacts, network, subprocess, installation, or file "
        "edits. Return only JSON with one source key containing executable Python, or one abstain_reason key.\n"
        + context
    )
    audit_repair_visible_payload(value)
    return value


base.prompt = prompt
_original_preflight = base.preflight


def preflight() -> dict:
    frozen = _original_preflight()
    frozen["schema"] = "e1c2-unified-dev-v4-flash-freeze"
    frozen["runner_sha256"] = _sha(Path(__file__))
    frozen["shared_runtime_sha256"] = _sha(ROOT / "evals/e1c_evaluation_2_unified_dev_v1.py")
    frozen["prompt_sha256"] = hashlib.sha256(prompt.__code__.co_code).hexdigest()
    return frozen


base.preflight = preflight


if __name__ == "__main__":
    base.main()
