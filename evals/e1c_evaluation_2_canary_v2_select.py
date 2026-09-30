"""Freeze DEV v4 method before choosing a second non-overlapping canary."""

from __future__ import annotations

import argparse
import hashlib
import json

from evals import e1c_evaluation_2_canary_select as prior
from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_dev_pilot import _save, _sha

METHOD = ROOT / "docs/research/E1C2_CANARY_V2_METHOD_FREEZE_2026-09-30.md"
FREEZE = ROOT / "data/e1c_evaluation_2_canary_v2_method_freeze.json"
IDENTITY = ROOT / "data/e1c_evaluation_2_canary_v2_identity.json"
SALT = "e1c-evaluation-2-independent-canary-v2-2026-09-30"
METHOD_FILES = (
    "evals/e1c_evaluation_2_canary_v2_select.py",
    "evals/e1c_evaluation_2_canary_v2_stage.py",
    "evals/e1c_evaluation_2_canary_v2_live.py",
    "evals/e1c_evaluation_2_canary_materialize.py",
    "evals/e1c_evaluation_2_canary_acquire.py",
    "evals/e1c_evaluation_2_admission.py",
    "evals/e1c_evaluation_2_unified_dev_v1.py",
    "evals/e1c_evaluation_2_unified_dev_v4.py",
    "evals/e1c_evaluation_2_unified_dev_v2_gold.py",
    "evals/e1c_evaluation_2_probe.py",
    "evals/e1c_evaluation_2_constructor_rule.py",
    "evals/e1c_evaluation_2_issue_input_v4.py",
    "evals/e1c_strict_v5_boundary.py",
    "docs/research/E1C2_CANARY_V2_METHOD_FREEZE_2026-09-30.md",
)


def method() -> dict:
    prior._checked_inputs()
    return {
        "schema": "e1c2-canary-method-freeze-v2",
        "status": "method_frozen_before_canary_selection",
        "method_files": {name: _sha(ROOT / name) for name in METHOD_FILES},
        "pool_sha256": _sha(prior.POOL),
        "old_canary_identity_sha256": _sha(prior.IDENTITY),
        "salt": SALT,
        "model": "deepseek-flash", "thinking": "disabled", "temperature": 0,
        "max_requests": 3, "max_requests_per_task": 1, "sdk_retries": 0,
        "max_output_tokens_per_request": 2600,
        "per_task_provider_token_cap": 14_000,
        "batch_provider_token_cap": 42_000,
        "candidate_count": 3, "minimum_trusted": 2,
        "provider_calls": 0, "canary_task_content_inspected": False,
    }


def freeze_method() -> dict:
    if IDENTITY.exists():
        raise FileExistsError("canary v2 identity already selected")
    value = method()
    if FREEZE.exists():
        if json.loads(FREEZE.read_bytes()) != value:
            raise ValueError("canary v2 method freeze differs")
    else:
        _save(FREEZE, value)
    return value


def freeze_identity() -> dict:
    frozen = json.loads(FREEZE.read_bytes())
    if frozen != method() or IDENTITY.exists():
        raise ValueError("method changed or canary v2 identity already selected")
    pool, dev = prior._checked_inputs()
    paths = set(prior._exclusion_paths(dev)) | {prior.IDENTITY}
    sources = []
    excluded = set(json.loads(prior.LEDGER.read_bytes())["identities"])
    for path in sorted(paths):
        raw = path.read_bytes()
        ids = prior._ids(json.loads(raw))
        excluded.update(ids)
        sources.append({"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "identity_count": len(ids)})
    prior_salt = prior.SALT
    try:
        prior.SALT = SALT
        rows = prior.select(pool, excluded)
    finally:
        prior.SALT = prior_salt
    if {row["instance_id"] for row in rows} & {row["instance_id"] for row in json.loads(prior.IDENTITY.read_bytes())["tasks"]}:
        raise ValueError("new canary overlaps previous canary")
    value = {
        "schema": "e1c2-canary-metadata-identity-v2",
        "role": "independent_canary_one_shot_no_replacement",
        "method_freeze_sha256": _sha(FREEZE),
        "source_revision": pool["source_revision"],
        "pool_sha256": _sha(prior.POOL), "salt": SALT,
        "selection_rule": "lowest sha256(salt+NUL+'repo'+NUL+repo), then lowest sha256(salt+NUL+'task'+NUL+instance_id)",
        "exclusion_sources": sources, "excluded_identity_count": len(excluded),
        "task_content_inspected": False, "outcome_inspected": False, "provider_calls": 0,
        "tasks": rows,
    }
    _save(IDENTITY, value)
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze-method", "select"))
    args = parser.parse_args()
    value = freeze_method() if args.command == "freeze-method" else freeze_identity()
    print(json.dumps({"status": value.get("status", value.get("role")), "task_count": len(value.get("tasks", [])), "provider_calls": 0}))
