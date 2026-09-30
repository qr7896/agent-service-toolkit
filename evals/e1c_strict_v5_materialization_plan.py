"""Create the post-freeze, pre-live materialization plan without executing it."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_freeze_certificate import MANIFEST, certify

OUT = ROOT / "data" / "e1c_strict_v5_materialization_plan.json"


def build(
    manifest_path: Path = MANIFEST,
    *,
    certificate: dict | None = None,
) -> dict:
    certificate = certificate or certify(manifest_path=manifest_path, output=None)
    if not certificate["ready"]:
        return {
            "schema": "e1c-strict-v5-materialization-plan-v1",
            "ready": False,
            "reason": "identity_freeze_not_certified",
            "provider_calls": 0,
            "task_content_materialized": False,
            "new_task_tree_touched": False,
            "actions": [],
        }
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actions = []
    for row in manifest["tasks"]:
        instance_id = row["instance_id"]
        actions.append({
            "instance_id": instance_id,
            "ordered_actions": [
                "fetch_public_statement_after_identity_freeze",
                "checkout_exact_base_commit",
                "verify_source_commit_identity",
                "pull_official_image",
                "run_independent_base_fail",
                "run_independent_gold_pass",
                "project_statement_to_strict_natural_language",
                "build_production_only_localization",
                "generate_pre_patch_probe_plan",
                "run_probe_twice_in_official_image_with_network_none",
                "audit_repair_visible_bundle_and_trace",
                "write_zero_provider_admission_row",
            ],
        })
    value = {
        "schema": "e1c-strict-v5-materialization-plan-v1",
        "ready": True,
        "reason": "identity_freeze_certified",
        "provider_calls": 0,
        "task_content_materialized": False,
        "new_task_tree_touched": False,
        "certificate_manifest_sha256": certificate["manifest_sha256"],
        "source_revision": certificate["source_revision"],
        "actions": actions,
    }
    value["plan_sha256"] = hashlib.sha256(
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
