"""Reproducer-focused blind runtime with fail-closed semantic/infra diagnosis."""

from __future__ import annotations

import ast
import builtins
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

from evals.e1c_blind_boundary import (
    AgentView,
    assert_agent_path,
    assert_agent_payload,
    audit_serialized_agent_trace,
    build_agent_view,
    read_agent_text,
)
from evals.e1c_blind_evidence import discover_original_test_probes, discover_test_roots

_FENCE = re.compile(r"```([A-Za-z0-9_-]*)\n(.*?)```", re.DOTALL)

_EXCEPTION = re.compile(r"\b(?:[A-Z][A-Za-z0-9_]*(?:Error|Exception)|NotImplementedError)\b")

_INFRA_PATTERNS = (
    "No module named pytest",
    "No module named nose",
    "pytest: command not found",
    "bin/test: not found",
    "could not import test module",
)


def expected_exception_names(statement: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(_EXCEPTION.findall(statement)))


def infrastructure_failure(result: dict) -> bool:
    tail = str(result.get("tail", ""))
    return any(pattern.lower() in tail.lower() for pattern in _INFRA_PATTERNS)


def reproducer_matches_issue(statement: str, result: dict, probe: dict | None = None) -> bool:
    if result.get("passed") or result.get("timed_out") or result.get("exit_code") in {None, 0}:
        return False
    if infrastructure_failure(result):
        return False
    if probe is not None and probe.get("repair_sensitive") is False:
        return False
    if result.get("kind") != "issue_snippet":
        matched = list((probe or {}).get("matched_symbols", []))
        tail = str(result.get("tail", "")).lower()
        return bool(matched) and any(symbol.lower() in tail for symbol in matched)
    expected = expected_exception_names(statement)
    if not expected:
        return True
    tail = str(result.get("tail", ""))
    return any(name in tail for name in expected)


def issue_python_snippets(statement: str, *, limit: int = 2) -> list[str]:
    snippets: list[str] = []
    for language, body in _FENCE.findall(statement):
        if language.lower() not in {"", "python", "py"}:
            continue
        lines = []
        for line in body.splitlines():
            stripped = line.strip()
            if stripped.startswith(("Traceback", "TypeError", "ValueError", "Error:", "Out[")):
                break
            line = re.sub(r"^\s*>>>\s?", "", line)
            line = re.sub(r"^\s*\.\.\.\s?", "", line)
            if re.match(r"^\s*In \[\d+\]:", line):
                line = line.split(":", 1)[1].lstrip()
            lines.append(line)
        snippet = "\n".join(lines).strip()
        if snippet and len(snippet) <= 6000:
            try:
                compile(snippet, "<issue-probe>", "exec")
            except SyntaxError:
                continue
            snippets.append(snippet)
        if len(snippets) == limit:
            break
    return snippets

def _undefined_names(source: str) -> list[str]:
    tree = ast.parse(source)
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
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            defined.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            defined.update(alias.asname or alias.name for alias in node.names)
    return sorted(loaded - defined - set(dir(builtins)))


def complete_snippet_from_statement(snippet: str, statement: str) -> str | None:
    assignments: list[str] = []
    for name in _undefined_names(snippet):
        patterns = (
            re.compile(rf"^\s*(?:-+>\s*)?\d+\s+({re.escape(name)}\s*=\s*.+)$", re.MULTILINE),
            re.compile(rf"^\s*({re.escape(name)}\s*=\s*[^\n]+)$", re.MULTILINE),
        )
        match = None
        for pattern in patterns:
            match = pattern.search(statement)
            if match:
                break
        if match:
            assignments.append(match.group(1).strip())
    if not assignments:
        return None
    lines = snippet.splitlines()
    insert_at = 0
    while insert_at < len(lines) and (
        lines[insert_at].startswith(("from ", "import ")) or not lines[insert_at].strip()
    ):
        insert_at += 1
    completed = "\n".join([*lines[:insert_at], *assignments, *lines[insert_at:]])
    try:
        compile(completed, "<issue-probe-completed>", "exec")
    except SyntaxError:
        return None
    return completed if completed != snippet else None


def issue_probe_candidates(statement: str, repo: str, *, limit: int = 4) -> list[dict]:
    package = repo.rsplit("/", 1)[-1].replace("-", "_").lower()
    candidates: list[dict] = []
    seen: set[str] = set()
    for snippet in issue_python_snippets(statement, limit=limit):
        variants = [("issue_snippet", snippet)]
        completed = complete_snippet_from_statement(snippet, statement)
        if completed:
            variants.insert(0, ("issue_snippet_completed", completed))
        for origin, content in variants:
            digest = hashlib.sha256(content.encode()).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            candidates.append(
                {
                    "kind": "issue_snippet",
                    "content": content,
                    "content_sha256": digest,
                    "origin": origin,
                    "repair_sensitive": package in content.lower(),
                }
            )
            if len(candidates) == limit:
                return candidates
    return candidates


def build_runtime_view(instance_id: str, statement: str, workspace: Path) -> AgentView:
    roots = discover_test_roots(workspace)
    return build_agent_view(
        instance_id=instance_id,
        problem_statement=statement,
        workspace=workspace,
        original_test_roots=roots,
    )


def _test_command(repo: str, path: str) -> list[str]:
    if repo == "django/django" and path.startswith("tests/") and path.endswith(".py"):
        relative = path[len("tests/") : -3]
        if relative.endswith("/__init__"):
            relative = relative[: -len("/__init__")]
        label = relative.replace("/", ".")
        return ["python", "tests/runtests.py", label, "--verbosity", "0"]
    if repo == "sympy/sympy":
        return ["python", "bin/test", path]
    return ["python", "-m", "pytest", "-q", path]


def freeze_probe_plan(row: dict, view: AgentView) -> dict:
    test_plan = discover_original_test_probes(view.problem_statement, view.workspace, limit=3)
    probes: list[dict] = []
    for candidate in issue_probe_candidates(view.problem_statement, row["repo"], limit=4):
        probes.append(
            {
                **candidate,
                "role": f"candidate_{len(probes)}",
                "purpose": "reproducer_candidate",
            }
        )
    for item in list(test_plan["probes"])[:3]:
        path = item["path"]
        assert_agent_path(
            view.workspace / path,
            workspace=view.workspace,
            original_test_roots=view.original_test_roots,
        )
        probes.append(
            {
                "kind": "original_test",
                "path": path,
                "command": _test_command(row["repo"], path),
                "matched_symbols": item.get("matched_symbols", []),
                "repair_sensitive": True,
                "role": f"candidate_{len(probes)}",
                "purpose": "reproducer_candidate",
            }
        )
    value = {
        "schema": "e1c-blind-reproducer-plan-v2",
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


def _docker_base(row: dict, *, name: str) -> list[str]:
    return [
        "docker",
        "run",
        "--rm",
        "--platform",
        "linux/amd64",
        "--network",
        "none",
        "--name",
        name,
    ]


def _source_guard(base_commit: str) -> str:
    return (
        "set -e; git config --global --add safe.directory /testbed; "
        f'git -C /testbed merge-base --is-ancestor "{base_commit}" HEAD; '
        "cd /testbed; "
    )


def run_probe(
    row: dict,
    probe: dict,
    artifact_dir: Path,
    *,
    patch_path: Path | None = None,
    timeout: int = 180,
) -> dict:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    name_seed = f"{row['instance_id']}:{probe['role']}:{probe['kind']}:{bool(patch_path)}"
    container_name = "e1c-blind-" + hashlib.sha256(name_seed.encode()).hexdigest()[:20]
    command = _docker_base(row, name=container_name)
    script = _source_guard(row["base_commit"])
    if patch_path is not None:
        patch_path = patch_path.resolve()
        if not patch_path.is_file():
            raise FileNotFoundError(patch_path)
        command += ["--mount", f"type=bind,source={patch_path},target=/candidate.patch,readonly"]
        script += "git apply --check /candidate.patch; git apply /candidate.patch; "
    if probe["kind"] == "issue_snippet":
        snippet_path = artifact_dir / f"{probe['role']}.issue_probe.py"
        snippet_path.write_text(probe["content"] + "\n", encoding="utf-8")
        command += ["--mount", f"type=bind,source={snippet_path.resolve()},target=/blind_probe.py,readonly"]
        script += "python /blind_probe.py"
    elif probe["kind"] == "original_test":
        script += " ".join(_shell_quote(part) for part in probe["command"])
    else:
        raise ValueError("unknown blind probe kind")
    command += [row["image"], "bash", "-lc", script]
    log_path = artifact_dir / f"{probe['role']}.{'post' if patch_path else 'pre'}.log"
    started = time.monotonic()
    timed_out = False
    with log_path.open("wb") as log:
        try:
            exit_code = subprocess.run(
                command,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
            ).returncode
        except subprocess.TimeoutExpired:
            timed_out, exit_code = True, None
            subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, timeout=30, check=False)
    data = log_path.read_bytes()
    result = {
        "schema": "e1c-blind-probe-result-v1",
        "role": probe["role"],
        "kind": probe["kind"],
        "exit_code": exit_code,
        "timed_out": timed_out,
        "passed": exit_code == 0 and not timed_out,
        "duration_seconds": round(time.monotonic() - started, 3),
        "log_sha256": hashlib.sha256(data).hexdigest(),
        "log_bytes": len(data),
        "tail": data.decode("utf-8", errors="replace")[-1800:],
        "plan_sha256": hashlib.sha256(
            json.dumps(probe, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }
    assert_agent_payload(result)
    audit_serialized_agent_trace(json.dumps(result, ensure_ascii=False))
    return result


def run_prepatch_probes(row: dict, view: AgentView, artifact_dir: Path) -> dict:
    plan = freeze_probe_plan(row, view)
    results = [run_probe(row, probe, artifact_dir) for probe in plan["probes"]]
    selected_role = None
    diagnoses = []
    for probe, result in zip(plan["probes"], results, strict=True):
        if result.get("timed_out"):
            reason = "timeout"
        elif infrastructure_failure(result):
            reason = "infrastructure_failure"
        elif result.get("passed"):
            reason = "candidate_passed"
        elif probe.get("repair_sensitive") is False:
            reason = "not_repair_sensitive"
        elif reproducer_matches_issue(view.problem_statement, result, probe):
            reason = "issue_matched_failure"
            if selected_role is None:
                selected_role = result["role"]
        else:
            reason = "semantic_mismatch"
        diagnoses.append({"role": result["role"], "reason": reason})
    if selected_role:
        status, no_reproducer_reason = "reproduced_failure", None
    elif any(item["reason"] == "infrastructure_failure" for item in diagnoses):
        status, no_reproducer_reason = "no_reproducer", "infrastructure_failure"
    elif any(item["reason"] == "semantic_mismatch" for item in diagnoses):
        status, no_reproducer_reason = "no_reproducer", "semantic_mismatch"
    elif any(item["reason"] == "candidate_passed" for item in diagnoses):
        status, no_reproducer_reason = "no_reproducer", "all_candidates_passed"
    elif diagnoses:
        status, no_reproducer_reason = "no_reproducer", diagnoses[0]["reason"]
    else:
        status, no_reproducer_reason = "no_reproducer", "no_candidates"
    value = {
        "schema": "e1c-blind-prepatch-probes-v2",
        "plan": plan,
        "results": results,
        "reproducer_status": status,
        "selected_reproducer_role": selected_role,
        "no_reproducer_reason": no_reproducer_reason,
        "diagnoses": diagnoses,
    }
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    audit_serialized_agent_trace(encoded)
    return {**value, "freeze_sha256": hashlib.sha256(encoded.encode()).hexdigest()}


def repair_probe_context(prepatch: dict) -> dict:
    selected_role = prepatch.get("selected_reproducer_role")
    reproducer = next((r for r in prepatch["results"] if r["role"] == selected_role), None)
    if prepatch["reproducer_status"] != "reproduced_failure" or reproducer is None:
        return {
            "status": "no_reproducer",
            "reason": prepatch.get("no_reproducer_reason", "unknown"),
        }
    return {
        "status": "reproduced_failure",
        "kind": reproducer["kind"],
        "exit_code": reproducer["exit_code"],
        "tail": reproducer["tail"],
        "log_sha256": reproducer["log_sha256"],
    }


def verify_candidate(
    row: dict,
    prepatch: dict,
    patch_path: Path,
    artifact_dir: Path,
) -> dict:
    results = []
    for probe in prepatch["plan"]["probes"]:
        post = run_probe(row, probe, artifact_dir, patch_path=patch_path)
        results.append(post)
    pre_by_role = {item["role"]: item for item in prepatch["results"]}
    post_by_role = {item["role"]: item for item in results}
    reasons = []
    selected_role = prepatch.get("selected_reproducer_role")
    reproducer_pre = pre_by_role.get(selected_role)
    reproducer_post = post_by_role.get(selected_role)
    if (
        reproducer_pre
        and not reproducer_pre["passed"]
        and not reproducer_pre["timed_out"]
        and reproducer_post
        and not reproducer_post["passed"]
    ):
        reasons.append("reproducer_still_fails")
    for probe, pre in zip(prepatch["plan"]["probes"], prepatch["results"], strict=True):
        if probe["kind"] != "original_test" or pre["role"] == selected_role or not pre["passed"]:
            continue
        post = post_by_role.get(pre["role"])
        if post and not post["passed"]:
            reasons.append("original_test_regression")
            break
    return {
        "schema": "e1c-blind-candidate-verification-v2",
        "passed": not reasons,
        "reasons": reasons,
        "results": results,
    }


def inspect_candidate(view: AgentView, path: str, symbol: str | None) -> dict:
    source = read_agent_text(view, path, max_chars=200_000)
    lines = source.splitlines()
    at = 0
    if symbol:
        patterns = (f"def {symbol}(", f"async def {symbol}(", f"class {symbol}(", f"class {symbol}:")
        for index, line in enumerate(lines):
            if line.lstrip().startswith(patterns):
                at = index
                break
        else:
            for index, line in enumerate(lines):
                if symbol in line:
                    at = index
                    break
    start = max(0, at - 12)
    return {
        "path": path,
        "symbol": symbol,
        "start_line": start + 1,
        "text": "\n".join(lines[start : at + 80])[:6000],
        "origin": "bounded_model_inspect",
        "source_sha256": hashlib.sha256((view.workspace / path).read_bytes()).hexdigest(),
    }


def _shell_quote(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_./:=+-]+", value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"
