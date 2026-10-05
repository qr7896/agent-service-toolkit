"""DEV-only response contracts, positive controls and bounded source coverage."""

from __future__ import annotations

import ast
import builtins
import json
import re
from pathlib import Path

from evals.e1c_blind_boundary import BlindBoundaryViolation
from evals.e1c_blind_evidence import _definition_index, extract_contract
from evals.e1c_evaluation_2_probe import input_json, validate_candidate
from evals.e1c_strict_v5_boundary import (
    assert_production_relative_path,
    audit_repair_visible_payload,
)

CONTRACT_KEYS = {"issue_quote", "expected_quote", "oracle", "setup_source", "control_action", "target_action", "assertion"}


def parse_response(raw: str, arm: str) -> dict:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("empty_response")
    fenced = re.fullmatch(r"\s*```json\s*\n(.*?)\n```\s*", raw, re.S)
    value = json.loads(fenced.group(1) if fenced else raw)
    if not isinstance(value, dict):
        raise ValueError("response_not_object")
    if set(value) == {"abstain_reason"}:
        reason = value["abstain_reason"]
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 1500:
            raise ValueError("invalid_abstention")
        return {"status": "abstained", "reason": reason}
    expected = {"source"} if arm == "A" else CONTRACT_KEYS
    if set(value) != expected:
        raise ValueError("response_schema_mismatch_or_input_echo")
    if any(not isinstance(item, str) for item in value.values()):
        raise ValueError("response_fields_must_be_strings")
    return {"status": "candidate", "payload": value}


def _block(source: str, *, action: bool) -> None:
    tree = ast.parse(source)
    if any(isinstance(node, (ast.Assert, ast.Try, ast.TryStar, ast.Raise)) for node in ast.walk(tree)):
        raise ValueError("setup_or_action_changes_or_swallows_the_oracle")
    if any(isinstance(node, ast.Name) and node.id.startswith("_e1c_") for node in ast.walk(tree)):
        raise ValueError("reserved_controller_name")
    if action and not any(isinstance(node, ast.Call) and (
        not isinstance(node.func, ast.Name) or node.func.id not in vars(builtins)
    ) for node in ast.walk(tree)):
        raise ValueError("action_has_no_real_call")


def build_pair(payload: dict, frozen: dict, workspace: Path | None = None) -> tuple[dict, dict]:
    if set(payload) != CONTRACT_KEYS or any(not isinstance(v, str) for v in payload.values()):
        raise ValueError("invalid_contract_fields")
    for key in ("issue_quote", "expected_quote"):
        if not 8 <= len(payload[key]) <= 1500 or payload[key] not in frozen["issue"]:
            raise ValueError("contract_quote_not_in_allowed_issue")
    if payload["oracle"] not in {"call_completes", "value_relation"}:
        raise ValueError("unsupported_oracle")
    for key in ("setup_source", "control_action", "target_action"):
        if len(payload[key]) > (4500 if key == "setup_source" else 1000):
            raise ValueError("contract_code_budget_exceeded")
        _block(payload[key], action=key != "setup_source")
    setup = payload["setup_source"].rstrip() + "\n"
    control_source = setup + payload["control_action"].strip() + "\n_e1c_control_done = True\nassert _e1c_control_done\n"
    target_source = setup + payload["target_action"].strip() + "\n"
    if payload["oracle"] == "call_completes":
        if payload["assertion"].strip():
            raise ValueError("call_completes_cannot_add_a_value_assertion")
        target_source += "_e1c_target_done = True\nassert _e1c_target_done\n"
    else:
        assertion = ast.parse(payload["assertion"])
        if (len(assertion.body) != 1 or not isinstance(assertion.body[0], ast.Assert)
                or not isinstance(assertion.body[0].test, ast.Compare)
                or len(payload["assertion"]) > 1000):
            raise ValueError("value_relation_requires_one_comparison_assertion")
        target_source += payload["assertion"].strip() + "\n"
    digest = audit_repair_visible_payload(payload)
    candidates = []
    for source in (control_source, target_source):
        candidate = validate_candidate(source, payload["issue_quote"], frozen, workspace=workspace)
        candidate["contract_sha256"] = digest
        candidates.append(candidate)
    return candidates[0], candidates[1]


def coverage_input(frozen: dict, workspace: Path) -> dict:
    """Task-label-free definition/traceback coverage; tests and oracle paths rejected."""
    workspace = workspace.resolve()
    issue = frozen["issue"]
    contract = extract_contract(issue)
    definitions, _ = _definition_index(workspace)
    requested = set(contract["symbols"])
    traces = re.findall(r'File ["\']([^"\']+\.py)["\'], line (\d+), in ([A-Za-z_]\w*)', issue)
    ranked = []
    for symbol, items in definitions.items():
        for item in items:
            matches = [(path, int(line)) for path, line, name in traces if name == symbol
                       and (path.replace("\\", "/").endswith(item["path"])
                            or Path(path).name == Path(item["path"]).name)
                       and item["start_line"] <= int(line) <= item["end_line"]]
            if not matches and symbol not in requested:
                continue
            try:
                path = assert_production_relative_path(item["path"])
                if not (workspace / path).resolve().is_relative_to(workspace):
                    raise ValueError("source path escaped workspace")
                lines = (workspace / path).read_text(encoding="utf-8", errors="replace").splitlines()
                center = matches[0][1] if matches else item["start_line"]
                start = max(item["start_line"], center - 6)
                end = min(item["end_line"], start + 45)
                text = "\n".join(lines[start - 1:end])[:2500]
                row = {"path": path, "symbol": symbol, "start_line": start,
                       "end_line": start + text.count("\n"), "source_sha256": item["source_sha256"], "text": text,
                       "origin": "issue_traceback_production" if matches else "issue_definition_coverage"}
                audit_repair_visible_payload(row)
            except BlindBoundaryViolation:
                continue
            ranked.append((0 if matches else 1, -int(symbol.lower() in issue.splitlines()[0].lower()), path, start, row))
    pool = [row for *_, row in sorted(ranked, key=lambda r: r[:4])] + [
        {**row, "text": row["text"][:2500]} for row in frozen["windows"]
    ]
    windows, seen = [], set()
    for row in pool:
        key = (row["path"], row.get("symbol"))
        if key in seen:
            continue
        try:
            assert_production_relative_path(row["path"])
            audit_repair_visible_payload(row)
        except BlindBoundaryViolation:
            continue
        proposed = {"issue": issue, "windows": [*windows, row]}
        if len(input_json(proposed)) > 23000:
            continue
        windows.append(row)
        seen.add(key)
        if len(windows) == 4:
            break
    found = requested.intersection(definitions)
    covered = {row.get("symbol") for row in windows}
    value = {"schema": "e1c2-contract-dev-input-v1", "issue": issue, "issue_sha256": frozen["issue_sha256"],
             "base_commit": frozen["base_commit"], "windows": windows, "candidate_paths": [r["path"] for r in windows],
             "candidate_count": len(windows), "status": "ready_for_generation" if windows else "no_production_candidate",
             "coverage": {"known_issue_symbols": sorted(found), "covered_symbols": sorted(found & covered),
                          "uncovered_symbols": sorted(found - covered), "traceback_clues": len(traces)}}
    value["input_sha256"] = audit_repair_visible_payload(value)
    return value
