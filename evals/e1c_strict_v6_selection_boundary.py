"""Freeze the strict-v6 identity-selection boundary before canary selection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT

SALT = "e1c-strict-v6-independent-canary"

LEDGER = ROOT / "data" / "e1c_strict_v5_contamination_ledger.json"
OUT = ROOT / "data" / "e1c_strict_v6_selection_boundary.json"
EXPECTED_MINIMUM = 244
TASK_REPO_REVISION = "3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d"
INVENTORY_REVISION = "02e7a74ffd0b707aab73d203fe87bdc7c76afc8e"


def build() -> dict:
    if not LEDGER.is_file():
        raise RuntimeError("strict-v6 contamination ledger missing")
    raw = LEDGER.read_bytes()
    ledger = json.loads(raw.decode("utf-8"))
    identities = ledger.get("identities")
    if not isinstance(identities, list) or len(identities) < EXPECTED_MINIMUM:
        raise RuntimeError("strict-v6 contamination ledger is incomplete")
    if len(identities) != len(set(identities)):
        raise RuntimeError("strict-v6 contamination ledger contains duplicate identities")
    computed_identity_sha = hashlib.sha256(
        json.dumps(identities, separators=(",", ":")).encode()
    ).hexdigest()
    if computed_identity_sha != ledger.get("identity_sha256"):
        raise RuntimeError("strict-v6 contamination identity hash mismatch")
    value = {
        "schema": "e1c-strict-v6-selection-boundary-v1",
        "provider_calls": 0,
        "task_content_inspected": False,
        "selection_salt": SALT,
        "contamination_count": len(identities),
        "contamination_identity_sha256": computed_identity_sha,
        "contamination_ledger_sha256": hashlib.sha256(raw).hexdigest(),
        "task_repo_revision": TASK_REPO_REVISION,
        "inventory_revision": INVENTORY_REVISION,
        "v5_canary_reuse_allowed": False,
        "outcome_conditioned_replacement_allowed": False,
    }
    value["boundary_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value


def write(output: Path = OUT) -> dict:
    value = build()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


def denylist() -> frozenset[str]:
    if not OUT.is_file():
        raise RuntimeError("strict-v6 selection boundary must be frozen first")
    boundary = json.loads(OUT.read_text(encoding="utf-8"))
    current = build()
    for key in (
        "selection_salt",
        "contamination_count",
        "contamination_identity_sha256",
        "contamination_ledger_sha256",
        "task_repo_revision",
        "inventory_revision",
        "boundary_sha256",
    ):
        if boundary.get(key) != current.get(key):
            raise RuntimeError(f"strict-v6 selection boundary drift: {key}")
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    return frozenset(ledger["identities"])


if __name__ == "__main__":
    print(json.dumps(write(), ensure_ascii=False, indent=2))
