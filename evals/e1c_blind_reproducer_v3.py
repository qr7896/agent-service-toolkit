"""Reproducer v3: transcript, exact-test-node and framework harness witnesses."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

from evals.e1c_blind_boundary import (
    AgentView,
    assert_agent_path,
    assert_agent_payload,
    audit_serialized_agent_trace,
)
from evals.e1c_blind_evidence import discover_original_test_probes, extract_contract
from evals.e1c_blind_reproducer_v2 import (
    build_runtime_view,
    infrastructure_failure,
    inspect_candidate,
    repair_probe_context,
    run_probe,
)

_PROMPT = re.compile(r"^\s*>>>\s?(.*)$")
_CONT = re.compile(r"^\s*\.\.\.\s?(.*)$")


def repl_transcript_snippets(statement: str, *, limit: int = 3) -> list[str]:
    groups: list[list[str]] = []
    current: list[str] = []
    for line in statement.splitlines():
        prompt = _PROMPT.match(line)
        cont = _CONT.match(line)
        if prompt:
            current.append(prompt.group(1))
            continue
        if cont and current:
            current.append(cont.group(1))
            continue
        if current and line.strip().startswith(("Traceback", "TypeError", "ValueError", "NotImplementedError")):
            groups.append(current)
            current = []
            continue
        if current and line.strip() and not line.startswith((" ", "\t")):
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    result: list[str] = []
    for group in groups:
        text = "\n".join(group).strip()
        if not text:
            continue
        try:
            compile(text, "<issue-repl>", "exec")
        except SyntaxError:
            continue
        if text not in result:
            result.append(text)
        if len(result) == limit:
            break
    return result


def _sympy_complete_exports(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source
    loaded = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    defined = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Param))
    }
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.update(alias.asname or alias.name for alias in node.names)
    candidates = sorted(name for name in loaded - defined - imports if name in {"I", "S", "Symbol", "symbols", "simplify"})
    if not candidates:
        return source
    return f"from sympy import {', '.join(candidates)}\n" + source


def consistency_witness_candidates(statement: str, repo: str) -> list[dict]:
    if repo != "sympy/sympy":
        return []
    commands: list[str] = []
    for line in statement.splitlines():
        match = _PROMPT.match(line)
        if match:
            commands.append(match.group(1).strip())
    assignment = next((line for line in commands if re.match(r"^[A-Za-z_]\w*\s*=", line)), None)
    if not assignment:
        return []
    variable = assignment.split("=", 1)[0].strip()
    plain = next((line for line in commands if re.fullmatch(rf"{re.escape(variable)}\.[A-Za-z_]\w*", line)), None)
    simplified = next(
        (
            line
            for line in commands
            if plain
            and re.fullmatch(
                rf"simplify\({re.escape(variable)}\)\.{re.escape(plain.split('.', 1)[1])}",
                line,
            )
        ),
        None,
    )
    if not plain or not simplified:
        return []
    source = _sympy_complete_exports(f"{assignment}\nassert {plain} == {simplified}")
    try:
        compile(source, "<issue-consistency-witness>", "exec")
    except SyntaxError:
        return []
    return [
        {
            "kind": "issue_snippet",
            "content": source,
            "content_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "origin": "issue_consistency_witness",
            "repair_sensitive": True,
            "semantic_contract": "issue_expression_consistency",
        }
    ]


def django_model_harness_candidates(statement: str, repo: str) -> list[dict]:
    if repo != "django/django" or "models.Model" not in statement or ".objects." not in statement:
        return []
    lines = statement.replace("\t", "    ").splitlines()
    start = next((i for i, line in enumerate(lines) if re.match(r"^class\s+\w+\(models\.Model\):", line.strip())), None)
    if start is None:
        return []
    end = next((i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith(">>>")), None)
    if end is None:
        return []
    model_lines = [line.rstrip() for line in lines[start:end] if line.strip()]
    repl = [m.group(1) for line in lines[end:] if (m := _PROMPT.match(line))]
    operation = next((line for line in repl if ".objects." in line), None)
    if not operation:
        return []
    normalized: list[str] = []
    current_class_indent = 0
    meta_seen = False
    inserted = False
    for line in model_lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if re.match(r"^class\s+\w+\(models\.Model\):", stripped):
            current_class_indent = indent
            meta_seen = False
            inserted = False
        if stripped == "class Meta:":
            meta_seen = True
            normalized.append(line)
            normalized.append(" " * (indent + 4) + "app_label = 'blind_repro'")
            inserted = True
            continue
        if indent <= current_class_indent and normalized and stripped.startswith("class ") and not inserted:
            normalized.extend([" " * (current_class_indent + 4) + "class Meta:", " " * (current_class_indent + 8) + "app_label = 'blind_repro'"])
        normalized.append(line)
    if not inserted and not meta_seen:
        normalized.extend(["    class Meta:", "        app_label = 'blind_repro'"])
    model_names = [
        re.match(r"^class\s+(\w+)\(models\.Model\):", line.strip()).group(1)
        for line in model_lines
        if re.match(r"^class\s+(\w+)\(models\.Model\):", line.strip())
    ]
    create = "\n".join(f"    editor.create_model({name})" for name in model_names)
    source = (
        "from django.conf import settings\n"
        "if not settings.configured:\n"
        "    settings.configure(INSTALLED_APPS=[], DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}, SECRET_KEY='blind')\n"
        "import django\n"
        "django.setup()\n"
        "from django.db import connection, models\n"
        + "\n".join(normalized)
        + "\nwith connection.schema_editor() as editor:\n"
        + create
        + "\n"
        + operation
    )
    try:
        compile(source, "<django-issue-harness>", "exec")
    except SyntaxError:
        return []
    return [
        {
            "kind": "issue_snippet",
            "content": source,
            "content_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "origin": "django_model_issue_harness",
            "repair_sensitive": True,
            "semantic_contract": "issue_operation_must_not_raise",
        }
    ]


def issue_probe_candidates(statement: str, repo: str, *, limit: int = 5) -> list[dict]:
    from evals.e1c_blind_reproducer_v2 import issue_probe_candidates as v2_candidates

    candidates: list[dict] = []
    seen: set[str] = set()
    raw = [
        *consistency_witness_candidates(statement, repo),
        *django_model_harness_candidates(statement, repo),
        *v2_candidates(statement, repo, limit=limit),
    ]
    package = repo.rsplit("/", 1)[-1].replace("-", "_").lower()
    for source in repl_transcript_snippets(statement, limit=3):
        if repo == "sympy/sympy":
            source = _sympy_complete_exports(source)
        raw.append(
            {
                "kind": "issue_snippet",
                "content": source,
                "content_sha256": hashlib.sha256(source.encode()).hexdigest(),
                "origin": "issue_repl_transcript",
                "repair_sensitive": package in source.lower() or repo == "sympy/sympy",
            }
        )
    for item in raw:
        digest = item["content_sha256"]
        if digest in seen:
            continue
        seen.add(digest)
        candidates.append(item)
        if len(candidates) == limit:
            break
    return candidates


def _node_source(lines: list[str], node: ast.AST) -> str:
    start = max(0, getattr(node, "lineno", 1) - 1)
    end = getattr(node, "end_lineno", getattr(node, "lineno", 1))
    return "\n".join(lines[start:end])


def exact_test_candidates(statement: str, workspace: Path, repo: str, *, limit: int = 4) -> list[dict]:
    contract = extract_contract(statement)
    symbols = {s.lower() for s in contract["symbols"]}
    title_terms = set(contract["title_terms"])
    file_plan = discover_original_test_probes(statement, workspace, limit=8)
    ranked: list[tuple[int, str, str, list[str], list[str]]] = []
    for file_item in file_plan["probes"]:
        path = assert_agent_path(workspace / file_item["path"], workspace=workspace)
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)
        except (OSError, SyntaxError):
            continue
        lines = source.splitlines()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                nodes = [(node.name, node)]
            elif isinstance(node, ast.ClassDef) and (node.name.startswith("Test") or node.name.endswith("Tests")):
                nodes = [
                    (f"{node.name}::{child.name}", child)
                    for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith("test")
                ]
            else:
                nodes = []
            for nodeid, target in nodes:
                text = _node_source(lines, target).lower()
                matched_symbols = sorted(symbol for symbol in symbols if symbol in text)
                matched_terms = sorted(term for term in title_terms if term in text or term in nodeid.lower())
                score = 30 * len(matched_symbols) + 8 * len(matched_terms)
                if score <= 0:
                    continue
                ranked.append((-score, file_item["path"], nodeid, matched_symbols[:8], matched_terms[:8]))
    ranked.sort()
    result = []
    for neg_score, path, nodeid, matched_symbols, matched_terms in ranked[:limit]:
        result.append(
            {
                "kind": "original_test",
                "path": path,
                "nodeid": nodeid,
                "command": _test_command(repo, path, nodeid),
                "matched_symbols": matched_symbols,
                "matched_terms": matched_terms,
                "target_score": -neg_score,
                "repair_sensitive": True,
                "origin": "exact_base_original_test_node",
            }
        )
    return result


def _test_command(repo: str, path: str, nodeid: str) -> list[str]:
    if repo == "django/django":
        relative = path[len("tests/") :] if path.startswith("tests/") else path
        module = relative[:-3].replace("/", ".") if relative.endswith(".py") else relative.replace("/", ".")
        target = nodeid.replace("::", ".")
        return ["python", "tests/runtests.py", f"{module}.{target}", "--verbosity", "0"]
    if repo == "sympy/sympy":
        target = nodeid.split("::")[-1]
        return ["python", "bin/test", path, "-k", target]
    return ["python", "-m", "pytest", "-q", f"{path}::{nodeid}"]


def freeze_probe_plan(row: dict, view: AgentView) -> dict:
    probes: list[dict] = []
    for candidate in issue_probe_candidates(view.problem_statement, row["repo"], limit=5):
        probes.append(
            {
                **candidate,
                "role": f"candidate_{len(probes)}",
                "purpose": "reproducer_candidate",
            }
        )
    for candidate in exact_test_candidates(view.problem_statement, view.workspace, row["repo"], limit=4):
        probes.append(
            {
                **candidate,
                "role": f"candidate_{len(probes)}",
                "purpose": "reproducer_candidate",
            }
        )
    value = {
        "schema": "e1c-blind-reproducer-plan-v3",
        "instance_id": row["instance_id"],
        "base_commit": row["base_commit"],
        "repo": row["repo"],
        "image": row["image"],
        "probes": probes,
        "status": "planned" if probes else "no_candidates",
    }
    assert_agent_payload(value)
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    audit_serialized_agent_trace(encoded)
    return {**value, "plan_sha256": hashlib.sha256(encoded.encode()).hexdigest()}


def _matches(statement: str, result: dict, probe: dict) -> bool:
    if result.get("passed") or result.get("timed_out") or result.get("exit_code") in {None, 0}:
        return False
    if infrastructure_failure(result) or probe.get("repair_sensitive") is False:
        return False
    if result.get("kind") == "issue_snippet":
        from evals.e1c_blind_reproducer_v2 import reproducer_matches_issue

        return reproducer_matches_issue(statement, result, probe)
    target = probe.get("nodeid", "").split("::")[-1].lower()
    tail = str(result.get("tail", "")).lower()
    return bool(target) and target in tail and int(probe.get("target_score", 0)) >= 16


def run_prepatch_probes(row: dict, view: AgentView, artifact_dir: Path) -> dict:
    plan = freeze_probe_plan(row, view)
    results: list[dict] = []
    executed_probes: list[dict] = []
    diagnoses: list[dict] = []
    selected_role = None
    for probe in plan["probes"]:
        result = run_probe(row, probe, artifact_dir, timeout=90)
        executed_probes.append(probe)
        results.append(result)
        if result.get("timed_out"):
            reason = "timeout"
        elif infrastructure_failure(result):
            reason = "infrastructure_failure"
        elif result.get("passed"):
            reason = "candidate_passed"
        elif probe.get("repair_sensitive") is False:
            reason = "not_repair_sensitive"
        elif _matches(view.problem_statement, result, probe):
            reason = "issue_matched_failure"
            selected_role = result["role"]
        else:
            reason = "semantic_mismatch"
        diagnoses.append({"role": result["role"], "reason": reason, "origin": probe.get("origin")})
        if selected_role:
            break
    if selected_role:
        executed_roles = {probe["role"] for probe in executed_probes}
        audit_probe = next(
            (
                probe
                for probe in plan["probes"]
                if probe["kind"] == "original_test" and probe["role"] not in executed_roles
            ),
            None,
        )
        if audit_probe is not None:
            audit_result = run_probe(row, audit_probe, artifact_dir, timeout=90)
            executed_probes.append(audit_probe)
            results.append(audit_result)
            if audit_result.get("timed_out"):
                audit_reason = "audit_timeout"
            elif infrastructure_failure(audit_result):
                audit_reason = "audit_infrastructure_failure"
            elif audit_result.get("passed"):
                audit_reason = "audit_passed"
            else:
                audit_reason = "audit_failed"
            diagnoses.append(
                {"role": audit_result["role"], "reason": audit_reason, "origin": audit_probe.get("origin")}
            )
    if selected_role:
        status, no_reproducer_reason = "reproduced_failure", None
    else:
        reasons = {item["reason"] for item in diagnoses}
        if not diagnoses:
            no_reproducer_reason = "no_candidates"
        elif reasons == {"candidate_passed"}:
            no_reproducer_reason = "all_candidates_passed"
        elif "semantic_mismatch" in reasons:
            no_reproducer_reason = "semantic_mismatch"
        elif "infrastructure_failure" in reasons:
            no_reproducer_reason = "infrastructure_failure"
        elif "timeout" in reasons:
            no_reproducer_reason = "timeout"
        else:
            no_reproducer_reason = sorted(reasons)[0]
        status = "no_reproducer"
    value = {
        "schema": "e1c-blind-prepatch-probes-v3",
        "plan": plan,
        "executed_probes": executed_probes,
        "results": results,
        "reproducer_status": status,
        "selected_reproducer_role": selected_role,
        "no_reproducer_reason": no_reproducer_reason,
        "diagnoses": diagnoses,
    }
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    audit_serialized_agent_trace(encoded)
    return {**value, "freeze_sha256": hashlib.sha256(encoded.encode()).hexdigest()}


def verify_candidate_v3(row: dict, prepatch: dict, patch_path: Path, artifact_dir: Path) -> dict:
    selected = prepatch.get("selected_reproducer_role")
    probes = prepatch.get("executed_probes", prepatch["plan"]["probes"])
    results = []
    for probe in probes:
        if probe["role"] != selected and probe["kind"] != "original_test":
            continue
        results.append(run_probe(row, probe, artifact_dir, patch_path=patch_path, timeout=90))
    post_by_role = {item["role"]: item for item in results}
    pre_by_role = {item["role"]: item for item in prepatch["results"]}
    reasons = []
    if selected:
        post = post_by_role.get(selected)
        if post is None or not post["passed"]:
            reasons.append("reproducer_still_fails")
    for probe in probes:
        if probe["kind"] != "original_test" or probe["role"] == selected:
            continue
        pre = pre_by_role.get(probe["role"])
        post = post_by_role.get(probe["role"])
        if pre and pre["passed"] and post and not post["passed"]:
            reasons.append("original_test_regression")
            break
    return {
        "schema": "e1c-blind-candidate-verification-v3",
        "passed": not reasons,
        "reasons": reasons,
        "results": results,
    }


__all__ = [
    "build_runtime_view",
    "freeze_probe_plan",
    "inspect_candidate",
    "repair_probe_context",
    "run_prepatch_probes",
    "verify_candidate_v3",
]
