"""Prepare the strict-v8 successor boundary without selecting a canary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT

SALT = "e1c-strict-v8-independent-canary"
BASE_LEDGER = ROOT / "data" / "e1c_strict_v5_contamination_ledger.json"
V6_MANIFEST = ROOT / "data" / "e1c_strict_v6_canary_manifest.json"
V7_MANIFEST = ROOT / "data" / "e1c_strict_v7_canary_manifest.json"
V7_SEAL = ROOT / "data" / "e1c_strict_v7_prelive_seal.json"
OUT = ROOT / "data" / "e1c_strict_v8_selection_boundary.json"
EXPECTED_BASE_MINIMUM = 244
TASK_REPO_REVISION = "3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d"
INVENTORY_REVISION = "02e7a74ffd0b707aab73d203fe87bdc7c76afc8e"


def _manifest_ids(path: Path, expected: int = 3) -> list[str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = document.get("tasks")
    if not isinstance(rows, list) or len(rows) != expected:
        raise RuntimeError(f"strict-v8 prerequisite manifest malformed: {path.name}")
    ids = [str(row.get("instance_id", "")) for row in rows if isinstance(row, dict)]
    if len(ids) != expected or len(set(ids)) != expected or any(not value for value in ids):
        raise RuntimeError(f"strict-v8 prerequisite identities malformed: {path.name}")
    return ids


def build() -> dict:
    ledger_raw = BASE_LEDGER.read_bytes()
    ledger = json.loads(ledger_raw.decode("utf-8"))
    identities = ledger.get("identities")
    if not isinstance(identities, list) or len(identities) < EXPECTED_BASE_MINIMUM:
        raise RuntimeError("strict-v8 base contamination ledger incomplete")
    if len(identities) != len(set(identities)):
        raise RuntimeError("strict-v8 base contamination ledger has duplicates")
    seal = json.loads(V7_SEAL.read_text(encoding="utf-8"))
    if seal.get("decision") != "seal_without_image_or_live":
        raise RuntimeError("strict-v8 requires strict-v7 to be sealed first")
    prior_ids = _manifest_ids(V6_MANIFEST) + _manifest_ids(V7_MANIFEST)
    merged = list(identities)
    for instance_id in prior_ids:
        if instance_id not in merged:
            merged.append(instance_id)
    identity_sha = hashlib.sha256(
        json.dumps(merged, separators=(",", ":")).encode()
    ).hexdigest()
    value = {
        "schema": "e1c-strict-v8-selection-boundary-v1",
        "provider_calls": 0,
        "task_content_inspected": False,
        "canary_selected": False,
        "mechanism_must_be_frozen_before_canary_selection": True,
        "selection_salt": SALT,
        "contamination_count": len(merged),
        "contamination_identity_sha256": identity_sha,
        "base_ledger_sha256": hashlib.sha256(ledger_raw).hexdigest(),
        "explicit_prior_canary_exclusions": prior_ids,
        "v6_manifest_sha256": hashlib.sha256(V6_MANIFEST.read_bytes()).hexdigest(),
        "v7_manifest_sha256": hashlib.sha256(V7_MANIFEST.read_bytes()).hexdigest(),
        "v7_seal_sha256": hashlib.sha256(V7_SEAL.read_bytes()).hexdigest(),
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


if __name__ == "__main__":
    print(json.dumps(write(), ensure_ascii=False, indent=2))
