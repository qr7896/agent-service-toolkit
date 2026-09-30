"""Generic source-behavior witnesses for strict-v8 development."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

_NEVER_USED = re.compile(
    r"(?i)\b(?P<symbol>[A-Za-z_]\w*)\b\s+(?:is|was|seems|appears)?\s*"
    r"(?:never|not)\s+(?:run|called|used|invoked|registered)\b"
)
_SHOULD_CALL = re.compile(
    r"(?i)\b(?P<owner>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\b.*?"
    r"\bshould\s+(?:call|invoke|use|run)\s+(?P<symbol>[A-Za-z_]\w*)\b"
)
_SHOULD_CLEAR = re.compile(
    r"(?i)\b(?P<symbol>[A-Za-z_]\w*)\(\)\s+"
    r"(?:should|must|is expected to)\s+clear\s+(?:the\s+)?"
    r"(?P<object>[A-Za-z_][A-Za-z0-9_ -]{0,80})"
)


@dataclass(frozen=True)
class SourceContract:
    kind: str
    symbol: str
    predicate: str
    candidate_path: str
    provenance: str = "projected_issue_plus_production_localization"
    benchmark_assertion_used: bool = False
    task_id_used: bool = False

    def to_dict(self) -> dict:
        value = asdict(self)
        value["schema"] = "e1c-strict-v8-source-contract-v1"
        value["witness_sha256"] = hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        audit_repair_visible_payload(value)
        return value


def _production_candidates(localization: dict, symbol: str) -> list[dict]:
    rows = []
    for row in localization.get("candidates", []):
        if not isinstance(row, dict):
            continue
        path = row.get("path")
        row_symbol = row.get("symbol")
        if not isinstance(path, str) or not path.endswith(".py"):
            continue
        if row_symbol == symbol or symbol in str(row.get("text", "")):
            rows.append(row)
    return rows


def _best_path(localization: dict, symbol: str) -> str | None:
    rows = _production_candidates(localization, symbol)
    if not rows:
        return None
    exact = [row for row in rows if row.get("symbol") == symbol]
    pool = exact or rows
    paths = []
    for row in pool:
        path = row["path"]
        if path not in paths:
            paths.append(path)
    return paths[0] if len(paths) == 1 else None


def extract_source_contracts(projected_issue: str, localization: dict) -> list[dict]:
    rows = []
    for match in _NEVER_USED.finditer(projected_issue):
        symbol = match.group("symbol")
        path = _best_path(localization, symbol)
        if path is None:
            continue
        contract = SourceContract(
            kind="source_usage",
            symbol=symbol,
            predicate="has_external_call_or_registration",
            candidate_path=path,
        ).to_dict()
        rows.append({"execution_ready": True, "origin": "never_used_claim", "witness": contract})
    for match in _SHOULD_CALL.finditer(projected_issue):
        symbol = match.group("symbol")
        path = _best_path(localization, symbol)
        if path is None:
            continue
        contract = SourceContract(
            kind="source_usage",
            symbol=symbol,
            predicate="has_external_call_or_registration",
            candidate_path=path,
        ).to_dict()
        rows.append({"execution_ready": True, "origin": "should_call_claim", "witness": contract})
    for match in _SHOULD_CLEAR.finditer(projected_issue):
        symbol = match.group("symbol")
        path = _best_path(localization, symbol)
        if path is None:
            continue
        contract = SourceContract(
            kind="source_effect",
            symbol=symbol,
            predicate="has_clear_or_invalidate_effect",
            candidate_path=path,
        ).to_dict()
        rows.append({"execution_ready": True, "origin": "should_clear_claim", "witness": contract})
    deduped = []
    seen = set()
    for row in rows:
        key = row["witness"]["witness_sha256"]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def evaluate_source_usage(workspace: Path, witness: dict) -> dict:
    symbol = str(witness["symbol"])
    candidate = str(witness["candidate_path"]).replace("\\", "/")
    calls = []
    registrations = []
    definitions = []
    for path in workspace.rglob("*.py"):
        relative = path.relative_to(workspace).as_posix()
        parts = {part.lower() for part in path.parts}
        if "tests" in parts or "test" in parts or "testing" in parts:
            continue
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (UnicodeDecodeError, SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == symbol:
                definitions.append({"path": relative, "line": getattr(node, "lineno", None)})
            if isinstance(node, ast.Call):
                func = node.func
                called = None
                if isinstance(func, ast.Name):
                    called = func.id
                elif isinstance(func, ast.Attribute):
                    called = func.attr
                if called == symbol:
                    calls.append({"path": relative, "line": getattr(node, "lineno", None)})
                for arg in list(node.args) + [kw.value for kw in node.keywords]:
                    if isinstance(arg, ast.Name) and arg.id == symbol:
                        registrations.append({"path": relative, "line": getattr(node, "lineno", None)})
    external_calls = [row for row in calls if row["path"] != candidate]
    external_regs = [row for row in registrations if row["path"] != candidate]
    passed = bool(external_calls or external_regs)
    value = {
        "schema": "e1c-strict-v8-source-usage-result-v1",
        "symbol": symbol,
        "candidate_path": candidate,
        "predicate": witness.get("predicate"),
        "definition_count": len(definitions),
        "external_call_count": len(external_calls),
        "external_registration_count": len(external_regs),
        "passed": passed,
        "sample_calls": external_calls[:8],
        "sample_registrations": external_regs[:8],
    }
    value["result_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value


def evaluate_source_effect(workspace: Path, witness: dict) -> dict:
    symbol = str(witness["symbol"])
    candidate = workspace / str(witness["candidate_path"])
    if not candidate.is_file():
        return {
            "schema": "e1c-strict-v8-source-effect-result-v1",
            "symbol": symbol,
            "candidate_path": str(witness["candidate_path"]),
            "predicate": witness.get("predicate"),
            "matched_effects": [],
            "passed": False,
            "reason": "candidate_source_missing",
        }
    try:
        tree = ast.parse(candidate.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, SyntaxError, OSError):
        return {
            "schema": "e1c-strict-v8-source-effect-result-v1",
            "symbol": symbol,
            "candidate_path": str(witness["candidate_path"]),
            "predicate": witness.get("predicate"),
            "matched_effects": [],
            "passed": False,
            "reason": "candidate_source_unparseable",
        }
    target = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol:
            target = node
            break
    if target is None:
        return {
            "schema": "e1c-strict-v8-source-effect-result-v1",
            "symbol": symbol,
            "candidate_path": str(witness["candidate_path"]),
            "predicate": witness.get("predicate"),
            "matched_effects": [],
            "passed": False,
            "reason": "target_symbol_missing",
        }
    effects = []

    class _DirectBodyVisitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name:
                lowered = name.lower()
                if "clear" in lowered or "invalidate" in lowered:
                    effects.append({"name": name, "line": getattr(node, "lineno", None)})
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            return None

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            return None

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            return None

    visitor = _DirectBodyVisitor()
    for statement in target.body:
        visitor.visit(statement)
    value = {
        "schema": "e1c-strict-v8-source-effect-result-v1",
        "symbol": symbol,
        "candidate_path": str(witness["candidate_path"]),
        "predicate": witness.get("predicate"),
        "matched_effects": effects[:8],
        "passed": bool(effects),
        "reason": "effect_found" if effects else "clear_or_invalidate_effect_missing",
    }
    value["result_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value
