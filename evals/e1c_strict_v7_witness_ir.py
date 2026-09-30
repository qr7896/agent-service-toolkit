"""Typed, fail-closed witness IR for strict-v7 mechanism development."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass, asdict

from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

ALLOWED_KINDS = {
    "call_result",
    "state_transition",
    "python_scenario",
    "artifact_predicate",
}
FORBIDDEN_PATH_PARTS = {
    "tests",
    "test",
    "testing",
    "gold.patch",
    "test.patch",
}
NETWORK_TOKENS = {
    "curl",
    "wget",
    "git clone",
    "http://",
    "https://",
    "requests.",
    "urllib.",
    "socket.",
}
SHELL_META = ("&&", "||", ";", "|", ">", "<", "$(", "`")


@dataclass(frozen=True)
class WitnessIR:
    kind: str
    source: str
    observable: str
    candidate_path: str
    provenance: str = "projected_issue_plus_production_localization"
    benchmark_assertion_used: bool = False
    task_id_used: bool = False

    def to_dict(self) -> dict:
        value = asdict(self)
        value["schema"] = "e1c-strict-v7-witness-ir-v1"
        value["witness_sha256"] = hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        audit_repair_visible_payload(value)
        return value


def _production_path(path: str) -> bool:
    normalized = path.replace("\\", "/").strip("/")
    if not normalized or normalized.startswith("."):
        return False
    parts = {part.lower() for part in normalized.split("/")}
    return not bool(parts & FORBIDDEN_PATH_PARTS)


def _safe_python(source: str) -> bool:
    if len(source) > 4000:
        return False
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    forbidden_nodes = (
        ast.Import,
        ast.ImportFrom,
        ast.With,
        ast.AsyncWith,
        ast.Lambda,
        ast.Global,
        ast.Nonlocal,
    )
    if any(isinstance(node, forbidden_nodes) for node in ast.walk(tree)):
        return False
    forbidden_names = {
        "eval",
        "exec",
        "compile",
        "open",
        "__import__",
        "input",
        "breakpoint",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in forbidden_names:
                return False
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return False
    lowered = source.lower()
    return not any(token in lowered for token in NETWORK_TOKENS)


def _safe_artifact_source(source: str) -> bool:
    lowered = source.lower().strip()
    if not lowered or len(source) > 1000:
        return False
    if any(token in lowered for token in NETWORK_TOKENS):
        return False
    if any(token in source for token in SHELL_META):
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9_./:=+@%,'\" -]+", source))


def validate(witness: WitnessIR) -> tuple[bool, str]:
    if witness.kind not in ALLOWED_KINDS:
        return False, "unsupported_kind"
    if witness.benchmark_assertion_used or witness.task_id_used:
        return False, "forbidden_benchmark_identity_or_assertion"
    if not _production_path(witness.candidate_path):
        return False, "non_production_candidate_path"
    if not witness.observable.strip() or len(witness.observable) > 1000:
        return False, "invalid_observable"
    if witness.kind in {"call_result", "state_transition", "python_scenario"}:
        if not _safe_python(witness.source):
            return False, "unsafe_python_source"
    elif witness.kind == "artifact_predicate":
        if not _safe_artifact_source(witness.source):
            return False, "unsafe_artifact_command"
    return True, "safe"


def freeze(witness: WitnessIR) -> dict:
    safe, reason = validate(witness)
    if not safe:
        return {
            "schema": "e1c-strict-v7-witness-freeze-v1",
            "status": "rejected",
            "reason": reason,
            "witness": None,
        }
    value = {
        "schema": "e1c-strict-v7-witness-freeze-v1",
        "status": "candidate",
        "reason": "safe_typed_witness",
        "witness": witness.to_dict(),
    }
    value["freeze_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    audit_repair_visible_payload(value)
    return value
