"""Freeze the E1-C evaluation_2 method, then select three metadata-only canaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_dev_pilot import _save, _sha

POOL = ROOT / "data/e1c_strict_v20_clean_metadata_pool.json"
LEDGER = ROOT / "data/e1c_strict_v5_contamination_ledger.json"
DEV = ROOT / "data/e1c_reproducer_dev12_identity.json"
PREREG = ROOT / "docs/research/E1C_EVALUATION_2_CANARY_PREREG_2026-09-29.md"
METHOD = ROOT / "docs/research/E1C2_CANARY_METHOD_FREEZE_2026-09-29.md"
FREEZE = ROOT / "data/e1c_evaluation_2_canary_method_freeze.json"
IDENTITY = ROOT / "data/e1c_evaluation_2_canary_identity.json"
SALT = "e1c-evaluation-2-independent-canary-2026-09-29"
KNOWN_SHA = {
    POOL: "7f1b59aff7411df40ec5d877f726bcb4161e7238e961cda859fb3b489f764ab2",
    LEDGER: "8468c2f4baa413351dd924f5d418a09857ea59d5a5e2890d3f405ff270e5022b",
    DEV: "3a374504aebcd88b935ac3d4f020a72a5e51a01f7fa46cf203fc7487c791fe4a",
}
METHOD_FILES = (
    "evals/e1c_evaluation_2_canary_select.py",
    "evals/e1c_evaluation_2_unified_dev_v1.py",
    "evals/e1c_evaluation_2_unified_dev_v2.py",
    "evals/e1c_evaluation_2_probe.py",
    "evals/e1c_evaluation_2_constructor_rule.py",
    "evals/e1c_evaluation_2_issue_input_v4.py",
    "evals/e1c_reproducer_dev_feedback.py",
    "evals/e1c_blind_evidence.py",
    "evals/e1c_strict_v5_boundary.py",
    "docs/research/E1C2_CANARY_METHOD_FREEZE_2026-09-29.md",
)
_IID = re.compile(r"^[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+-[0-9]+$")


def _ids(value: object) -> set[str]:
    if isinstance(value, str):
        return {value} if _IID.fullmatch(value) else set()
    if isinstance(value, list):
        return set().union(*(_ids(item) for item in value)) if value else set()
    if isinstance(value, dict):
        return set().union(*(_ids(item) for item in value.values())) if value else set()
    return set()


def _checked_inputs() -> tuple[dict, dict]:
    for path, digest in KNOWN_SHA.items():
        if _sha(path) != digest:
            raise ValueError(f"preregistered metadata source changed: {path.name}")
    pool, dev = json.loads(POOL.read_bytes()), json.loads(DEV.read_bytes())
    if (
        pool.get("tree_truncated") is not False
        or pool.get("task_content_inspected") is not False
        or pool.get("source_revision") != dev.get("source_revision")
        or len(dev.get("tasks", [])) != 12
    ):
        raise ValueError("frozen metadata pool or DEV12 identity invalid")
    return pool, dev


def method() -> dict:
    _checked_inputs()
    if not METHOD.is_file():
        raise ValueError("complete method document is missing")
    return {
        "schema": "e1c2-canary-method-freeze-v1",
        "status": "method_frozen_before_canary_selection",
        "selection_prereg_sha256": _sha(PREREG),
        "method_files": {name: _sha(ROOT / name) for name in METHOD_FILES},
        "model": "deepseek-flash", "thinking": "disabled", "temperature": 0,
        "max_requests": 3, "max_requests_per_task": 1, "sdk_retries": 0,
        "max_output_tokens_per_request": 2600,
        "per_task_provider_token_cap": 14000,
        "batch_provider_token_cap": 42000,
        "candidate_count": 3, "minimum_trusted": 2,
        "provider_calls": 0, "canary_task_content_inspected": False,
    }


def _exclusion_paths(dev: dict) -> list[Path]:
    data = ROOT / "data"
    paths = {LEDGER, DEV, ROOT / "data/e1c_candidate_manifest.json"}
    for path in data.glob("*.json"):
        if any(word in path.name for word in ("canary", "cohort", "manifest", "identity")):
            paths.add(path)
    for row in dev["exclusion_files"]:
        path = ROOT / row["path"]
        if _sha(path) != row["sha256"]:
            raise ValueError(f"frozen DEV exclusion changed: {path.name}")
        paths.add(path)
    codex = ROOT / ".codex/e1c"
    if codex.is_dir():
        for path in codex.rglob("*.json"):
            if path.name in {"identity.json", "selector_identity.json", "candidate_manifest.json", "final_admitted_manifest.json"}:
                paths.add(path)
    paths.discard(IDENTITY)
    return sorted(paths, key=lambda path: path.as_posix())


def select(pool: dict, excluded: set[str]) -> list[dict]:
    """Exactly the repository-then-task salted ordering in the preregistration."""
    by_repo: dict[str, list[dict]] = {}
    for row in pool["tasks"]:
        iid = row["instance_id"]
        if iid not in excluded:
            by_repo.setdefault(iid.split("__", 1)[0], []).append(row)

    def rank(kind: str, value: str) -> tuple[str, str]:
        return hashlib.sha256((SALT + "\0" + kind + "\0" + value).encode()).hexdigest(), value

    repos = sorted(by_repo, key=lambda repo: rank("repo", repo))[:3]
    if len(repos) != 3:
        raise ValueError("fewer than three eligible repositories")
    rows = [sorted(by_repo[repo], key=lambda row: rank("task", row["instance_id"]))[0] for repo in repos]
    if len({row["instance_id"] for row in rows}) != 3:
        raise ValueError("selected canary identity duplicated")
    return rows


def freeze_method() -> dict:
    if IDENTITY.exists():
        raise ValueError("canary identity already exists; method cannot be re-frozen")
    value = method()
    if FREEZE.exists():
        if json.loads(FREEZE.read_bytes()) != value:
            raise ValueError("existing method freeze differs")
    else:
        _save(FREEZE, value)
    return value


def freeze_identity() -> dict:
    frozen = json.loads(FREEZE.read_bytes())
    if frozen != method():
        raise ValueError("method changed after freeze; refuse identity selection")
    if IDENTITY.exists():
        raise FileExistsError("canary identity already sealed; no reselection")
    pool, dev = _checked_inputs()
    sources = []
    excluded: set[str] = set(json.loads(LEDGER.read_bytes())["identities"])
    for path in _exclusion_paths(dev):
        raw = path.read_bytes()
        ids = _ids(json.loads(raw))
        excluded.update(ids)
        sources.append({"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "identity_count": len(ids)})
    rows = select(pool, excluded)
    value = {
        "schema": "e1c2-canary-metadata-identity-v1",
        "role": "independent_canary_one_shot_no_replacement",
        "method_freeze_sha256": _sha(FREEZE),
        "source_revision": pool["source_revision"],
        "pool_sha256": _sha(POOL), "salt": SALT,
        "selection_rule": "lowest sha256(salt+NUL+'repo'+NUL+repo), then lowest sha256(salt+NUL+'task'+NUL+instance_id)",
        "exclusion_sources": sources, "excluded_identity_count": len(excluded),
        "task_content_inspected": False, "outcome_inspected": False, "provider_calls": 0,
        "tasks": rows,
    }
    _save(IDENTITY, value)
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze-method", "select"))
    command = parser.parse_args().command
    value = freeze_method() if command == "freeze-method" else freeze_identity()
    print(json.dumps({"status": value.get("status", value.get("role")), "task_count": len(value.get("tasks", [])), "provider_calls": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
