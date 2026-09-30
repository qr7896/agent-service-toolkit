"""Immutable hash seal for legacy E1-C artifacts reused only as history/audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT

OUT = ROOT / "data" / "e1c_strict_v5_legacy_artifact_seal.json"

LEGACY_PATHS = (
    ".codex/e1c/candidate_manifest.json",
    ".codex/e1c/candidate_manifest.sha256",
    ".codex/e1c/final_admitted_manifest.json",
    ".codex/e1c/final_admitted_manifest.sha256",
    "data/e1c_candidate_manifest.json",
    "data/formal_e1_n30_summary.json",
    "data/wave_b_cohort_manifest.json",
    "data/wave_b_cohort_metadata.json",
    ".codex/e1c/e1c-blind-canary-v1/identity.json",
    ".codex/e1c/e1c-blind-canary-v1/provider_calls.jsonl",
    ".codex/e1c/e1c-blind-canary-v1/result.json",
    ".codex/e1c/e1c-blind-canary-v1/resume_identity.json",
    ".codex/e1c/e1c-blind-canary-v1/state.json",
    ".codex/e1c/e1c-blind-postb4-c4-prep-v1/identity.json",
    ".codex/e1c/e1c-blind-postb4-c4-prep-v1/prepared.json",
    ".codex/e1c/e1c-blind-postb4-c4-prep-v1/selector_identity.json",
    ".codex/e1c/e1c-blind-postb4-c4-v1/identity.json",
    ".codex/e1c/e1c-blind-postb4-c4-v1/provider_calls.jsonl",
    ".codex/e1c/e1c-blind-postb4-c4-v1/result.json",
    ".codex/e1c/e1c-blind-postb4-c4-v1/state.json",
    ".codex/e1c/e1c-blind-reproducer-c4r-prep-v1/identity.json",
    ".codex/e1c/e1c-blind-reproducer-c4r-prep-v1/prepared.json",
    ".codex/e1c/e1c-blind-reproducer-c4r-prep-v1/selector_identity.json",
    ".codex/e1c/e1c-blind-reproducer-c4r-v3-prep-v1/identity.json",
    ".codex/e1c/e1c-blind-reproducer-c4r-v3-prep-v1/prepared.json",
    ".codex/e1c/e1c-blind-reproducer-c4r-v3-prep-v1/selector_identity.json",
    ".codex/e1c/e1c-blind-reproducer-v3-dev-diagnostic/summary.json",
    ".codex/e1c/e1c-blind-reproducer-v3-dev2-diagnostic/summary.json",
    ".codex/e1c/e1c-blind-reproducer-v4-dev-diagnostic-v1/result.json",
    "data/e1c_blind_reproducer_v4_canary_manifest.template.json",
    "data/e1c_fresh30_v4_prereg_plan.json",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seal_sha(entries: list[dict]) -> str:
    canonical = [
        {"path": row["path"], "sha256": row["sha256"]}
        for row in sorted(entries, key=lambda item: item["path"])
    ]
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def build(output: Path = OUT) -> dict:
    present = []
    missing = []
    for relative in LEGACY_PATHS:
        path = ROOT / relative
        if not path.is_file():
            missing.append(relative)
            continue
        present.append(
            {
                "path": relative,
                "sha256": _sha(path),
                "size_bytes": path.stat().st_size,
            }
        )
    result = {
        "schema": "e1c-strict-v5-legacy-artifact-seal-v1",
        "ready": not missing,
        "reason": "legacy_artifacts_sealed" if not missing else "legacy_artifacts_missing",
        "sealed_file_count": len(present),
        "missing_file_count": len(missing),
        "missing_paths": missing,
        "seal_sha256": _seal_sha(present),
        "entries": present,
        "legacy_content_read_for_runtime": False,
        "legacy_results_authoritative_for_v5": False,
        "provider_calls": 0,
        "live_model_run": False,
        "live_allowed": False,
        "c5_allowed": False,
        "fresh30_allowed": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def verify(seal_path: Path = OUT) -> dict:
    frozen = json.loads(seal_path.read_text(encoding="utf-8"))
    changed = []
    missing = []
    for row in frozen.get("entries", []):
        path = ROOT / row["path"]
        if not path.is_file():
            missing.append(row["path"])
        elif _sha(path) != row["sha256"]:
            changed.append(row["path"])
    match = not changed and not missing and frozen.get("ready") is True
    return {
        "schema": "e1c-strict-v5-legacy-artifact-seal-verify-v1",
        "match": match,
        "seal_sha256": frozen.get("seal_sha256"),
        "changed_paths": sorted(changed),
        "missing_paths": sorted(missing),
        "provider_calls": 0,
        "live_model_run": False,
        "live_allowed": False,
        "c5_allowed": False,
        "fresh30_allowed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "verify"))
    args = parser.parse_args()
    result = build() if args.command == "build" else verify()
    print(json.dumps(result, indent=2))
    if (args.command == "build" and not result["ready"]) or (
        args.command == "verify" and not result["match"]
    ):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
