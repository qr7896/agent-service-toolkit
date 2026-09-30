"""Prepare the successor canary denylist without selecting or opening task content."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT

SALT = "e1c-strict-v7-independent-canary"
LEDGER = ROOT / "data" / "e1c_strict_v5_contamination_ledger.json"
V6_MANIFEST = ROOT / "data" / "e1c_strict_v6_canary_manifest.json"
OUT = ROOT / "data" / "e1c_strict_v7_selection_boundary.json"
EXPECTED_BASE_MINIMUM = 244
TASK_REPO_REVISION = "3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d"
INVENTORY_REVISION = "02e7a74ffd0b707aab73d203fe87bdc7c76afc8e"


def build() -> dict:
    ledger_raw = LEDGER.read_bytes()
    ledger = json.loads(ledger_raw.decode("utf-8"))
    base = ledger.get("identities")
    if not isinstance(base, list) or len(base) < EXPECTED_BASE_MINIMUM:
        raise RuntimeError("strict-v7 base contamination ledger is incomplete")
    if len(base) != len(set(base)):
        raise RuntimeError("strict-v7 base contamination ledger has duplicates")

    manifest_raw = V6_MANIFEST.read_bytes()
    manifest = json.loads(manifest_raw.decode("utf-8"))
    rows = manifest.get("tasks")
    if not isinstance(rows, list) or len(rows) != 3:
        raise RuntimeError("strict-v7 requires the sealed three-task v6 manifest")
    v6_ids = [str(row.get("instance_id", "")) for row in rows if isinstance(row, dict)]
    if len(v6_ids) != 3 or any(not value for value in v6_ids) or len(set(v6_ids)) != 3:
        raise RuntimeError("strict-v7 v6 canary identity is malformed")

    identities = list(base)
    for instance_id in v6_ids:
        if instance_id not in identities:
            identities.append(instance_id)
    identity_sha = hashlib.sha256(
        json.dumps(identities, separators=(",", ":")).encode()
    ).hexdigest()
    value = {
        "schema": "e1c-strict-v7-selection-boundary-v1",
        "provider_calls": 0,
        "task_content_inspected": False,
        "canary_selected": False,
        "mechanism_must_be_frozen_before_canary_selection": True,
        "selection_salt": SALT,
        "contamination_count": len(identities),
        "contamination_identity_sha256": identity_sha,
        "base_ledger_sha256": hashlib.sha256(ledger_raw).hexdigest(),
        "v6_manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "explicit_v6_exclusions": v6_ids,
        "task_repo_revision": TASK_REPO_REVISION,
        "inventory_revision": INVENTORY_REVISION,
        "prior_canary_reuse_allowed": False,
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
        raise RuntimeError("strict-v7 selection boundary must be frozen first")
    frozen = json.loads(OUT.read_text(encoding="utf-8"))
    current = build()
    for key in (
        "selection_salt",
        "contamination_count",
        "contamination_identity_sha256",
        "base_ledger_sha256",
        "v6_manifest_sha256",
        "task_repo_revision",
        "inventory_revision",
        "boundary_sha256",
    ):
        if frozen.get(key) != current.get(key):
            raise RuntimeError(f"strict-v7 selection boundary drift: {key}")
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    identities = list(ledger["identities"])
    for instance_id in current["explicit_v6_exclusions"]:
        if instance_id not in identities:
            identities.append(instance_id)
    return frozenset(identities)


if __name__ == "__main__":
    print(json.dumps(write(), ensure_ascii=False, indent=2))
