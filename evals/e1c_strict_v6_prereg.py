"""Freeze the strict-v6 mechanism identity before selecting a new canary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v6_runtime import mechanism_identity

OUT = ROOT / "data" / "e1c_strict_v6_prereg.json"
MECHANISM_FILES = (
    ROOT / "evals" / "e1c_strict_v5_boundary.py",
    ROOT / "evals" / "e1c_strict_v5_runtime.py",
    ROOT / "evals" / "e1c_strict_v6_probe.py",
    ROOT / "evals" / "e1c_strict_v6_runtime.py",
)


def build() -> dict:
    identity = mechanism_identity(MECHANISM_FILES)
    value = {
        "schema": "e1c-strict-v6-reproducer-prereg-v1",
        "provider_calls": 0,
        "task_content_selected_after_mechanism_freeze": True,
        "parent_v5_seal": "data/e1c_strict_v5_admission_seal.json",
        "v5_canary_reuse_allowed": False,
        "selection_salt": "e1c-strict-v6-independent-canary",
        "canary_task_count": 3,
        "minimum_trusted_reproducers": 2,
        "live_allowed_before_admission": False,
        "mechanism": identity,
        "supported_relation_classes": [
            "return_equals",
            "return_instead_of",
            "equality_expression",
            "contains",
            "not_contains",
            "raises",
            "raises_instead_of",
        ],
        "unsupported_behavior": "fail_closed_no_reproducer",
    }
    value["prereg_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value


def write(output: Path = OUT) -> dict:
    value = build()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


if __name__ == "__main__":
    print(json.dumps(write(), ensure_ascii=False, indent=2))
