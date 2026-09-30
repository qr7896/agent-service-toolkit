"""Blind-side probe execution and bounded verification without benchmark oracle mounts."""

from __future__ import annotations

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


def expected_exception_names(statement: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(_EXCEPTION.findall(statement)))


def reproducer_matches_issue(statement: str, result: dict) -> bool:
    if result.get("passed") or result.get("timed_out") or result.get("exit_code") in {None, 0}:
        return False
    if result.get("kind") != "issue_snippet":
        return True
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
    return ["python", "-m", "pytest", "-q", path]


def freeze_probe_plan(row: dict, view: AgentView) -> dict:
    test_plan = discover_original_test_probes(view.problem_statement, view.workspace, limit=3)
    snippets = issue_python_snippets(view.problem_statement, limit=2)
    probes = []
    if snippets:
        probes.append(
            {
                "kind": "issue_snippet",
                "content": snippets[0],
                "content_sha256": hashlib.sha256(snippets[0].encode()).hexdigest(),
                "role": "reproducer",
            }
        )
    tests = list(test_plan["probes"])
    if tests:
        path = tests.pop(0)["path"]
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
                "role": "reproducer" if not probes else "audit",
            }
        )
    if tests:
        path = tests.pop(0)["path"]
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
                "role": "audit",
            }
        )
    value = {
        "schema": "e1c-blind-probe-plan-v1",
        "instance_id": row["instance_id"],
        "base_commit": row["base_commit"],
        "repo": row["repo"],
        "image": row["image"],
        "probes": probes,
        "status": "planned" if probes else "no_reproducer",
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
    results = []
    for probe in plan["probes"]:
        results.append(run_probe(row, probe, artifact_dir))
    reproducer = next((r for r in results if r["role"] == "reproducer"), None)
    status = "no_reproducer"
    if reproducer is not None and reproducer_matches_issue(view.problem_statement, reproducer):
        status = "reproduced_failure"
    value = {
        "schema": "e1c-blind-prepatch-probes-v1",
        "plan": plan,
        "results": results,
        "reproducer_status": status,
    }
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    audit_serialized_agent_trace(encoded)
    return {**value, "freeze_sha256": hashlib.sha256(encoded.encode()).hexdigest()}


def repair_probe_context(prepatch: dict) -> dict:
    reproducer = next((r for r in prepatch["results"] if r["role"] == "reproducer"), None)
    if prepatch["reproducer_status"] != "reproduced_failure" or reproducer is None:
        return {"status": "no_reproducer"}
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
    reproducer_pre = pre_by_role.get("reproducer")
    reproducer_post = post_by_role.get("reproducer")
    if (
        reproducer_pre
        and not reproducer_pre["passed"]
        and not reproducer_pre["timed_out"]
        and reproducer_post
        and not reproducer_post["passed"]
    ):
        reasons.append("reproducer_still_fails")
    audit_pre = pre_by_role.get("audit")
    audit_post = post_by_role.get("audit")
    if audit_pre and audit_pre["passed"] and audit_post and not audit_post["passed"]:
        reasons.append("original_test_regression")
    return {
        "schema": "e1c-blind-candidate-verification-v1",
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
