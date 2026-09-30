"""Zero-provider strict-v5 localization and blind repair bundle."""

from __future__ import annotations

import hashlib
from pathlib import Path

from evals.e1c_blind_boundary import BlindBoundaryViolation
from evals.e1c_blind_evidence import extract_contract, lexical_windows, structural_windows
from evals.e1c_strict_v5_boundary import (
    assert_production_relative_path,
    audit_repair_visible_payload,
    project_issue,
)
from evals.e1c_strict_v5_probe import freeze_probe_plan


def _candidate(item: dict, *, rank: int) -> dict:
    path = assert_production_relative_path(str(item["path"]))
    text = str(item.get("text", ""))
    return {
        "path": path,
        "symbol": item.get("symbol"),
        "start_line": int(item.get("start_line", 1)),
        "end_line": int(item.get("end_line", item.get("start_line", 1))),
        "origin": str(item.get("origin", "unknown")),
        "depth": int(item.get("depth", 0)),
        "source_sha256": str(item["source_sha256"]),
        "read_cost": len(text),
        "rank": rank,
        "text": text,
    }


def localize(projected_issue: str, workspace: Path, *, limit: int = 6) -> dict:
    workspace = workspace.resolve()
    structural = structural_windows(projected_issue, workspace, limit=limit)
    lexical = lexical_windows(projected_issue, workspace, limit=limit)
    merged: list[dict] = []
    seen: set[tuple[str, object, int, int]] = set()
    for item in [*structural, *lexical]:
        normalized = _candidate(item, rank=len(merged) + 1)
        key = (
            normalized["path"],
            normalized["symbol"],
            normalized["start_line"],
            normalized["end_line"],
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(normalized)
        if len(merged) == limit:
            break
    total_read_cost = sum(int(row["read_cost"]) for row in merged)
    value = {
        "schema": "e1c-strict-v5-localization-v1",
        "candidate_paths": [row["path"] for row in merged],
        "candidates": merged,
        "candidate_count": len(merged),
        "total_read_cost": total_read_cost,
        "max_candidate_count": limit,
        "abstain_reason": None if merged else "no_production_candidate",
    }
    value["localization_sha256"] = audit_repair_visible_payload(value)
    return value


def build_bundle(
    *,
    statement: str,
    workspace: Path,
    base_commit: str,
    forbidden_values: tuple[str, ...] = (),
    limit: int = 6,
) -> dict:
    projection = project_issue(statement)
    localization = localize(projection.text, workspace, limit=limit)
    probe_plan = freeze_probe_plan(projection.text, localization)
    payload = {
        "schema": "e1c-strict-v5-agent-bundle-v1",
        "issue": projection.text,
        "issue_projection_sha256": projection.sha256,
        "source_commit": base_commit,
        "contract": extract_contract(projection.text),
        "localization": localization,
        "probe_plan": probe_plan,
        "candidate_paths": localization["candidate_paths"],
        "inspect_budget": {"max_calls": 1, "max_chars": 4000, "max_unique_paths": 1},
    }
    payload["bundle_sha256"] = audit_repair_visible_payload(
        payload,
        forbidden_values=forbidden_values,
    )
    return payload


def inspect_candidate(
    bundle: dict,
    workspace: Path,
    path: str,
    symbol: str | None = None,
    *,
    prior_inspections: tuple[dict, ...] = (),
) -> dict:
    workspace = workspace.resolve()
    allowed = set(bundle.get("candidate_paths", []))
    normalized = assert_production_relative_path(path)
    budget = bundle.get("inspect_budget", {})
    max_calls = int(budget.get("max_calls", 1))
    max_unique_paths = int(budget.get("max_unique_paths", 1))
    if len(prior_inspections) >= max_calls:
        raise BlindBoundaryViolation("strict-v5 inspect call budget exceeded")
    prior_paths = {str(item.get("path")) for item in prior_inspections}
    if normalized not in prior_paths and len(prior_paths) >= max_unique_paths:
        raise BlindBoundaryViolation("strict-v5 inspect unique-path budget exceeded")
    if normalized not in allowed:
        raise BlindBoundaryViolation("strict-v5 inspect path is not a frozen candidate")
    target = (workspace / normalized).resolve(strict=True)
    if target.is_symlink():
        raise BlindBoundaryViolation("strict-v5 inspect rejects symlink")
    source = target.read_text(encoding="utf-8", errors="replace")
    lines = source.splitlines()
    candidate = next(
        (
            row
            for row in bundle["localization"]["candidates"]
            if row["path"] == normalized and (symbol is None or row.get("symbol") == symbol)
        ),
        None,
    )
    if candidate is None:
        raise BlindBoundaryViolation("strict-v5 inspect symbol is not frozen")
    start = max(1, int(candidate["start_line"]))
    end = min(len(lines), max(start, int(candidate["end_line"])))
    max_chars = int(budget.get("max_chars", 4000))
    text = "\n".join(lines[start - 1 : end])[:max_chars]
    result = {
        "path": normalized,
        "symbol": candidate.get("symbol"),
        "start_line": start,
        "end_line": end,
        "text": text,
        "source_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "read_cost": len(text),
    }
    audit_repair_visible_payload(result)
    return result
