"""Task-agnostic strict-v7 typed witness extraction from public issue prose."""

from __future__ import annotations

import ast
import builtins
import hashlib
import json
import re

from evals.e1c_strict_v6_probe import candidate_witnesses as v6_candidate_witnesses
from evals.e1c_strict_v7_witness_ir import WitnessIR, freeze

_PYTHON_FENCE = re.compile(r"```(?:python|py)\s*\n(?P<body>.*?)```", re.I | re.S)
_SHELL_FENCE = re.compile(r"```(?:bash|sh|shell|console)\s*\n(?P<body>.*?)```", re.I | re.S)
_STATE = re.compile(
    r"(?i)(?P<call>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\(\)\s+"
    r"(?:should|must|is expected to)\s+"
    r"(?P<verb>clear|reset|invalidate|remove|preserve)\s+"
    r"(?:the\s+)?(?P<object>[A-Za-z_][A-Za-z0-9_ -]{1,80})"
)


def _candidates(localization: dict) -> list[dict]:
    rows = localization.get("candidates", [])
    return [
        row
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("path"), str)
        and row["path"].endswith(".py")
    ]


def _symbols(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    values = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            values.add(node.id)
        elif isinstance(node, ast.Attribute):
            values.add(node.attr)
    return values


def _loaded_names(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    loaded = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    assigned = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    return loaded - assigned - set(dir(builtins))


def _associate_python(source: str, localization: dict) -> dict | None:
    symbols = _symbols(source)
    scores: dict[str, tuple[int, dict]] = {}
    for row in _candidates(localization):
        symbol = row.get("symbol")
        if isinstance(symbol, str) and symbol in symbols:
            count = source.count(symbol)
            current = scores.get(row["path"])
            if current is None or count > current[0]:
                scores[row["path"]] = (count, row)
    if not scores:
        return None
    best = max(score for score, _ in scores.values())
    winners = [row for score, row in scores.values() if score == best]
    if len(winners) == 1:
        return winners[0]
    return None


def _scenario_execution_ready(source: str, candidate: dict, localization: dict) -> bool:
    unresolved = _loaded_names(source)
    if not unresolved:
        return True
    path = candidate.get("path")
    available = {
        row.get("symbol")
        for row in _candidates(localization)
        if row.get("path") == path and isinstance(row.get("symbol"), str)
    }
    return unresolved <= available


def _indented_python_blocks(projected_issue: str) -> list[str]:
    blocks = []
    current = []
    for line in projected_issue.splitlines():
        if line.startswith("\t") or line.startswith("    "):
            current.append(line[1:] if line.startswith("\t") else line[4:])
        else:
            if len(current) >= 2:
                body = "\n".join(current).strip()
                try:
                    ast.parse(body)
                except SyntaxError:
                    pass
                else:
                    blocks.append(body)
            current = []
    if len(current) >= 2:
        body = "\n".join(current).strip()
        try:
            ast.parse(body)
        except SyntaxError:
            pass
        else:
            blocks.append(body)
    return blocks


def _single_candidate(localization: dict) -> dict | None:
    rows = _candidates(localization)
    unique = {row["path"]: row for row in rows}
    if len(unique) == 1:
        return next(iter(unique.values()))
    return None


def _clean_shell(body: str) -> str | None:
    commands = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("$"):
            line = line[1:].strip()
        if line.startswith(">"):
            continue
        commands.append(line)
    if len(commands) != 1:
        return None
    return commands[0]


def _row(frozen: dict, *, execution_ready: bool, origin: str) -> dict:
    value = {
        "origin": origin,
        "execution_ready": execution_ready,
        "freeze": frozen,
    }
    value["row_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value


def typed_candidates(projected_issue: str, localization: dict, *, limit: int = 8) -> list[dict]:
    rows: list[dict] = []

    for legacy in v6_candidate_witnesses(projected_issue, localization, limit=limit):
        source = legacy["call"] + "\n"
        observable = f"{legacy['relation']}:{legacy['expected']}"
        frozen = freeze(
            WitnessIR(
                kind="call_result",
                source=source,
                observable=observable,
                candidate_path=legacy["candidate_path"],
            )
        )
        if frozen["status"] == "candidate":
            rows.append(_row(frozen, execution_ready=True, origin="strict_v6_literal_relation"))

    python_bodies = [match.group("body").strip() for match in _PYTHON_FENCE.finditer(projected_issue)]
    python_bodies.extend(_indented_python_blocks(projected_issue))
    for body in python_bodies:
        candidate = _associate_python(body, localization)
        if candidate is None:
            continue
        frozen = freeze(
            WitnessIR(
                kind="python_scenario",
                source=body + "\n",
                observable="scenario_exit_code == 0",
                candidate_path=candidate["path"],
            )
        )
        if frozen["status"] == "candidate":
            rows.append(
                _row(
                    frozen,
                    execution_ready=_scenario_execution_ready(body, candidate, localization),
                    origin="projected_issue_python_scenario",
                )
            )

    for match in _STATE.finditer(projected_issue):
        symbol = match.group("call").split(".")[-1]
        candidates = [row for row in _candidates(localization) if row.get("symbol") == symbol]
        unique = {row["path"]: row for row in candidates}
        if len(unique) != 1:
            continue
        candidate = next(iter(unique.values()))
        frozen = freeze(
            WitnessIR(
                kind="state_transition",
                source=f"{symbol}()\n",
                observable=(
                    f"postcondition:{match.group('verb').lower()}:"
                    f"{match.group('object').strip().lower()}"
                ),
                candidate_path=candidate["path"],
            )
        )
        if frozen["status"] == "candidate":
            rows.append(_row(frozen, execution_ready=False, origin="projected_issue_state_relation"))

    single = _single_candidate(localization)
    if single is not None:
        for match in _SHELL_FENCE.finditer(projected_issue):
            command = _clean_shell(match.group("body"))
            if command is None:
                continue
            frozen = freeze(
                WitnessIR(
                    kind="artifact_predicate",
                    source=command,
                    observable="local_artifact_predicate_requires_freeze",
                    candidate_path=single["path"],
                )
            )
            if frozen["status"] == "candidate":
                rows.append(_row(frozen, execution_ready=False, origin="projected_issue_shell_fence"))

    deduped = []
    seen = set()
    for row in rows:
        witness = row["freeze"].get("witness") or {}
        key = witness.get("witness_sha256")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
        if len(deduped) == limit:
            break
    return deduped


def freeze_typed_plan(projected_issue: str, localization: dict) -> dict:
    rows = typed_candidates(projected_issue, localization)
    executable = [row for row in rows if row["execution_ready"]]
    value = {
        "schema": "e1c-strict-v7-typed-witness-plan-v1",
        "status": "candidate_executable_witnesses" if executable else "no_executable_reproducer",
        "typed_candidates": rows,
        "candidate_count": len(rows),
        "executable_candidate_count": len(executable),
        "trusted_reproducer": False,
        "provider_calls": 0,
        "benchmark_assertion_used": False,
    }
    value["plan_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value
