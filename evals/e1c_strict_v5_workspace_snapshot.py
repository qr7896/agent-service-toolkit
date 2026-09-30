"""Reproducibility snapshot for the strict-v5 pre-live workspace identity."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from evals.e1c_admission import ROOT

OUT = ROOT / "data" / "e1c_strict_v5_workspace_snapshot.json"

STATIC_DATA = (
    "data/e1c_strict_v5_canary_manifest.json",
    "data/e1c_strict_v5_freeze_certificate.json",
    "data/e1c_strict_v5_metadata_audit.json",
    "data/e1c_strict_v5_contamination_ledger.json",
)
PROTOCOL_DOCS = (
    "docs/research/E1C_STRICT_BLIND_DEV30_TO_FRESH30_PLAYBOOK.md",
)
MUTABLE_DIAGNOSTIC_PREFIXES = (
    "data/e1c_strict_v5_blob_preflight",
    "data/e1c_strict_v5_cache_",
    "data/e1c_strict_v5_image_",
    "data/e1c_strict_v5_infra_gate",
    "data/e1c_strict_v5_protocol_consistency",
    "data/e1c_strict_v5_transport_trend",
    "data/e1c_strict_v5_admission_seal",
    "data/e1c_strict_v5_canary_admission",
    "data/e1c_strict_v5_grader_materialization",
    "data/e1c_strict_v5_materialization_plan",
    "data/e1c_strict_v5_official_image_acquisition",
    "data/e1c_strict_v5_postfreeze_identity",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"git_{args[0]}_failed")
    return completed.stdout.strip()


def _relevant_paths() -> tuple[list[str], list[str]]:
    identity = sorted(
        {
            *(
                path.relative_to(ROOT).as_posix()
                for path in (ROOT / "evals").glob("e1c_strict_v5*.py")
            ),
            *(
                path.relative_to(ROOT).as_posix()
                for path in (ROOT / "tests").glob("test_e1c_strict_v5*.py")
            ),
            *(path for path in STATIC_DATA if (ROOT / path).is_file()),
            *(path for path in PROTOCOL_DOCS if (ROOT / path).is_file()),
        }
    )
    mutable = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "data").glob("e1c_strict_v5*")
        if path.is_file()
        and any(
            path.relative_to(ROOT).as_posix().startswith(prefix)
            for prefix in MUTABLE_DIAGNOSTIC_PREFIXES
        )
        and path.relative_to(ROOT).as_posix() not in identity
    )
    return identity, mutable


def _status_map() -> dict[str, str]:
    result: dict[str, str] = {}
    raw = _git("status", "--porcelain=v1", "--untracked-files=all")
    for line in raw.splitlines():
        if len(line) < 4:
            continue
        status = line[:2]
        path = line[3:].replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        result[path] = status
    return result


def _entries(paths: list[str], status_map: dict[str, str]) -> list[dict]:
    return [
        {
            "path": path,
            "sha256": _sha(ROOT / path),
            "git_status": status_map.get(path, "  "),
            "tracked_clean": path not in status_map,
        }
        for path in paths
    ]


def _identity_sha(entries: list[dict]) -> str:
    canonical = [
        {"path": row["path"], "sha256": row["sha256"]}
        for row in sorted(entries, key=lambda item: item["path"])
    ]
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def build(output: Path = OUT) -> dict:
    identity_paths, mutable_paths = _relevant_paths()
    status_map = _status_map()
    identity_entries = _entries(identity_paths, status_map)
    mutable_entries = _entries(mutable_paths, status_map)
    head = _git("rev-parse", "HEAD")
    relevant_dirty = [
        row for row in identity_entries if row["tracked_clean"] is False
    ]
    snapshot = {
        "schema": "e1c-strict-v5-workspace-snapshot-v1",
        "head": head,
        "head_is_sufficient_identity": not relevant_dirty,
        "workspace_identity_required": bool(relevant_dirty),
        "identity_sha256": _identity_sha(identity_entries),
        "identity_file_count": len(identity_entries),
        "relevant_dirty_count": len(relevant_dirty),
        "relevant_dirty_paths": [row["path"] for row in relevant_dirty],
        "identity_entries": identity_entries,
        "mutable_diagnostic_file_count": len(mutable_entries),
        "mutable_diagnostic_entries": mutable_entries,
        "mutable_diagnostics_excluded_from_identity_sha": True,
        "provider_calls": 0,
        "live_model_run": False,
        "live_allowed": False,
        "c5_allowed": False,
        "fresh30_allowed": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    return snapshot


def verify(snapshot_path: Path = OUT) -> dict:
    frozen = json.loads(snapshot_path.read_text(encoding="utf-8"))
    identity_paths, _ = _relevant_paths()
    status_map = _status_map()
    current_entries = _entries(identity_paths, status_map)
    current_sha = _identity_sha(current_entries)
    frozen_paths = {row["path"] for row in frozen.get("identity_entries", [])}
    current_paths = {row["path"] for row in current_entries}
    frozen_hashes = {
        row["path"]: row["sha256"] for row in frozen.get("identity_entries", [])
    }
    changed = sorted(
        path
        for path in frozen_paths & current_paths
        if frozen_hashes.get(path)
        != next(row["sha256"] for row in current_entries if row["path"] == path)
    )
    added = sorted(current_paths - frozen_paths)
    missing = sorted(frozen_paths - current_paths)
    match = (
        current_sha == frozen.get("identity_sha256")
        and not added
        and not missing
        and not changed
    )
    return {
        "schema": "e1c-strict-v5-workspace-snapshot-verify-v1",
        "match": match,
        "frozen_identity_sha256": frozen.get("identity_sha256"),
        "current_identity_sha256": current_sha,
        "changed_paths": changed,
        "added_paths": added,
        "missing_paths": missing,
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
    if args.command == "verify" and not result["match"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
