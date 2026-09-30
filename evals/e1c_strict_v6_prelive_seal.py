"""Seal strict-v6 at the zero-provider candidate-reproducer gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT

ASSESSMENT = ROOT / "data" / "e1c_strict_v6_postfreeze_assessment.json"
OUT = ROOT / "data" / "e1c_strict_v6_prelive_seal.json"


def seal(output: Path = OUT) -> dict:
    assessment_bytes = ASSESSMENT.read_bytes()
    assessment = json.loads(assessment_bytes.decode("utf-8"))
    rows = assessment.get("rows", [])
    frozen_instance_ids = [
        str(row["instance_id"]) for row in rows if isinstance(row, dict) and row.get("instance_id")
    ]
    candidate_count = int(assessment.get("candidate_reproducer_task_count", 0))
    minimum = int(assessment.get("minimum_candidate_reproducer_tasks", 2))
    materialization_complete = (
        int(assessment.get("source_ready_count", 0)) == len(rows) == 3
        and int(assessment.get("projection_supported_count", 0)) == 3
    )
    gate_failed = materialization_complete and candidate_count < minimum
    value = {
        "schema": "e1c-strict-v6-prelive-seal-v1",
        "provider_calls": 0,
        "live_model_run": False,
        "frozen_instance_ids": frozen_instance_ids,
        "postfreeze_materialization_complete": materialization_complete,
        "candidate_reproducer_task_count": candidate_count,
        "minimum_candidate_reproducer_tasks": minimum,
        "candidate_reproducer_gate_failed": gate_failed,
        "image_pull_allowed": False,
        "official_admission_allowed": False,
        "live_allowed": False,
        "decision": "seal_without_image_or_live" if gate_failed else "not_sealed",
        "reason": (
            "candidate_reproducer_minimum_unreachable_on_frozen_v6_canary"
            if gate_failed
            else "postfreeze_assessment_not_decisive"
        ),
        "outcome_conditioned_replacement_allowed": False,
        "same_canary_reuse_for_mechanism_tuning_allowed": False,
        "next_mechanism_must_use_new_independent_canary": gate_failed,
        "large_image_download_avoided": gate_failed,
        "assessment_sha256": hashlib.sha256(assessment_bytes).hexdigest(),
        "assessment_summary_sha256": assessment.get("summary_sha256"),
    }
    value["seal_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


if __name__ == "__main__":
    print(json.dumps(seal(), ensure_ascii=False, indent=2))
