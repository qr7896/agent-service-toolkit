"""Flash-only DEV contrast: issue-derived expected behavior with minimal constructed fixtures."""

from __future__ import annotations

import hashlib
from pathlib import Path

from evals import e1c_evaluation_2_unified_dev_v1 as base
from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_dev_pilot import _sha
from evals.e1c_evaluation_2_probe import input_json
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

base.RUN_ID = "e1c2-unified-dev-v2-flash"
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
        "Using only this public issue and exact-base production-source windows, write a standalone Python "
        "script with an explicit assert that exercises the stated failing behavior through the real public "
        "API. The report may omit setup variables or a full runnable example: construct the smallest valid "
        "fixture needed to exercise the same input type and preconditions, using production API signatures "
        "shown in source. The expected behavior must still come from the public issue, never from an "
        "invented requirement. Do not produce a fake warning, exception, or production result yourself; "
        "the assertion must observe the real API. If no issue-grounded behavioral oracle exists, abstain. "
        "Do not read tests, hidden patches, grader artifacts or task IDs, edit production code, install "
        "packages, call network, or use subprocess/I/O helpers. Return only JSON with one source key "
        "containing executable Python, or one abstain_reason key.\n" + context
    )
    audit_repair_visible_payload(value)
    return value


base.prompt = prompt
_original_preflight = base.preflight


def preflight() -> dict:
    frozen = _original_preflight()
    frozen["schema"] = "e1c2-unified-dev-v2-flash-freeze"
    frozen["runner_sha256"] = _sha(Path(__file__))
    frozen["shared_runtime_sha256"] = _sha(ROOT / "evals/e1c_evaluation_2_unified_dev_v1.py")
    frozen["prompt_sha256"] = hashlib.sha256(prompt.__code__.co_code).hexdigest()
    return frozen


# ponytail: process-local CLI override reuses the sealed v1 execution path;
# parameterize a shared runner only if another variant is actually needed.
base.preflight = preflight


if __name__ == "__main__":
    base.main()
