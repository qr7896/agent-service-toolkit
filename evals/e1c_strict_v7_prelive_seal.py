"""Seal strict-v7 before image acquisition after the zero-provider candidate gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT

ASSESSMENT = ROOT / "data" / "e1c_strict_v7_postfreeze_assessment.json"
OUT = ROOT / "data" / "e1c_strict_v7_prelive_seal.json"


def seal(output: Path = OUT) -> dict:
    raw = ASSESSMENT.read_bytes()
    assessment = json.loads(raw.decode("utf-8"))
    certificate = assessment.get("identity_certificate") or {}
    ids = certificate.get("instance_ids") or []
    source_ready = int(assessment.get("source_ready_count", 0))
    projection_ready = int(assessment.get("projection_supported_count", 0))
    executable = int(assessment.get("executable_candidate_task_count", 0))
    minimum = int(assessment.get("minimum_executable_candidate_tasks", 2))
    prerequisites_complete = len(ids) == 3 and source_ready == 3 and projection_ready == 3
    gate_failed = prerequisites_complete and executable < minimum
    value = {
        "schema": "e1c-strict-v7-prelive-seal-v1",
        "provider_calls": 0,
        "live_model_run": False,
        "frozen_instance_ids": ids,
        "postfreeze_materialization_complete": prerequisites_complete,
        "typed_candidate_task_count": int(assessment.get("typed_candidate_task_count", 0)),
        "executable_candidate_task_count": executable,
        "minimum_executable_candidate_tasks": minimum,
        "candidate_gate_failed": gate_failed,
        "image_pull_allowed": False,
        "official_admission_allowed": False,
        "live_allowed": False,
        "c5_allowed": False,
        "dev30_allowed": False,
        "fresh30_allowed": False,
        "decision": "seal_without_image_or_live" if gate_failed else "not_sealed",
        "reason": (
            "executable_candidate_minimum_unreachable_on_frozen_v7_canary"
            if gate_failed
            else "postfreeze_assessment_not_decisive"
        ),
        "outcome_conditioned_replacement_allowed": False,
        "same_canary_reuse_for_mechanism_tuning_allowed": False,
        "next_mechanism_must_use_new_independent_canary": gate_failed,
        "large_image_download_avoided": gate_failed,
        "assessment_sha256": hashlib.sha256(raw).hexdigest(),
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
