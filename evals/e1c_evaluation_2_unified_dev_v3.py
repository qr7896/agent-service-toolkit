"""Flash DEV contrast: one issue-grounded observable, no extra assertions."""

from __future__ import annotations

import hashlib
from pathlib import Path

from evals import e1c_evaluation_2_unified_dev_v1 as base
from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_dev_pilot import _sha
from evals.e1c_evaluation_2_probe import input_json
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

base.RUN_ID = "e1c2-unified-dev-v3-flash"
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
        "Using only this public issue and exact-base production-source windows, decide whether the report "
        "states a concrete observable failing behavior and expected behavior. A discussion, RFC, or broad "
        "feature proposal without such an oracle requires abstention. Otherwise write one standalone Python "
        "script with exactly one assert on that issue behavior through the real public API. If the issue "
        "includes runnable example code, preserve its input type, values, and preconditions and replace its "
        "observation with the assert. If setup is omitted, construct only a minimal valid fixture consistent "
        "with the production API signatures shown; do not use dummy objects with missing required members. "
        "Do not add an unrelated or stronger assertion, fabricate a warning/error/result, mock production "
        "behavior, or use hidden patches, tests, task IDs, grader artifacts, network, subprocess, installation, or file "
        "edits. If a sound issue-grounded oracle or valid fixture cannot be determined, abstain. "
        "Return only JSON with one source key containing executable Python, or one abstain_reason key.\n" + context
    )
    audit_repair_visible_payload(value)
    return value


base.prompt = prompt
_original_preflight = base.preflight


def preflight() -> dict:
    frozen = _original_preflight()
    frozen["schema"] = "e1c2-unified-dev-v3-flash-freeze"
    frozen["runner_sha256"] = _sha(Path(__file__))
    frozen["shared_runtime_sha256"] = _sha(ROOT / "evals/e1c_evaluation_2_unified_dev_v1.py")
    frozen["prompt_sha256"] = hashlib.sha256(prompt.__code__.co_code).hexdigest()
    return frozen


base.preflight = preflight


if __name__ == "__main__":
    base.main()
