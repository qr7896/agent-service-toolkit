"""Task-agnostic executable probes derived only from projected issue prose."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

_RETURN = re.compile(
    r"(?i)(?P<call>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\([^()\n]{0,160}\))\s+"
    r"(?:should|must|is expected to)\s+(?:return|returns)\s+"
    r"(?P<expected>None|True|False|-?\d+(?:\.\d+)?|'[^'\n]*'|\"[^\"\n]*\")"
)
_RAISE = re.compile(
    r"(?i)(?P<call>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\([^()\n]{0,160}\))\s+"
    r"(?:should|must|is expected to)\s+raise\s+(?P<expected>[A-Z]\w*(?:Error|Exception))"
)


def _safe_call(source: str) -> tuple[ast.Call, str] | None:
    try:
        node = ast.parse(source, mode="eval").body
    except SyntaxError:
        return None
    if not isinstance(node, ast.Call) or node.keywords:
        return None
    if not isinstance(node.func, ast.Name):
        return None
    allowed = (ast.Constant, ast.Tuple, ast.List, ast.Dict, ast.Set)
    for arg in node.args:
        if not isinstance(arg, allowed):
            return None
        try:
            ast.literal_eval(arg)
        except (ValueError, TypeError):
            return None
    return node, node.func.id


def _module_name(path: str) -> str | None:
    if not path.endswith(".py"):
        return None
    parts = path[:-3].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts or any(not part.isidentifier() for part in parts):
        return None
    return ".".join(parts)


def candidate_probes(projected_issue: str, localization: dict, *, limit: int = 3) -> list[dict]:
    relations: list[tuple[int, str, str, str]] = []
    for match in _RETURN.finditer(projected_issue):
        relations.append((match.start(), "return_equals", match.group("call"), match.group("expected")))
    for match in _RAISE.finditer(projected_issue):
        relations.append((match.start(), "raises", match.group("call"), match.group("expected")))
    relations.sort()
    candidates = localization.get("candidates", [])
    probes: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for _, relation, call, expected in relations:
        parsed = _safe_call(call)
        if parsed is None:
            continue
        _, symbol = parsed
        matches = [
            row
            for row in candidates
            if row.get("symbol") == symbol or symbol.lower() in str(row.get("text", "")).lower()
        ]
        for row in matches:
            module = _module_name(str(row["path"]))
            if not module:
                continue
            key = (module, call, relation + ":" + expected)
            if key in seen:
                continue
            seen.add(key)
            probe = {
                "kind": "natural_language_contract",
                "relation": relation,
                "call": call,
                "expected": expected,
                "symbol": symbol,
                "module": module,
                "candidate_path": row["path"],
                "source_sha256": row["source_sha256"],
                "provenance": "projected_issue_plus_production_localization",
                "benchmark_assertion_used": False,
                "task_id_used": False,
            }
            encoded = json.dumps(probe, sort_keys=True, separators=(",", ":"))
            probe["probe_sha256"] = hashlib.sha256(encoded.encode()).hexdigest()
            audit_repair_visible_payload(probe)
            probes.append(probe)
            if len(probes) == limit:
                return probes
    return probes


def freeze_probe_plan(projected_issue: str, localization: dict) -> dict:
    probes = candidate_probes(projected_issue, localization)
    value = {
        "schema": "e1c-strict-v5-executable-probe-plan-v1",
        "status": "candidate_executable_probes" if probes else "no_reproducer",
        "probes": probes,
        "trusted_reproducer": False,
        "no_reproducer_reason": None if probes else "no_safe_natural_language_contract",
    }
    value["plan_sha256"] = audit_repair_visible_payload(value)
    return value


def render_probe(probe: dict) -> str:
    module = json.dumps(probe["module"])
    symbol = json.dumps(probe["symbol"])
    call = probe["call"]
    relation = probe["relation"]
    expected = probe["expected"]
    prefix = (
        "import importlib\n"
        f"module = importlib.import_module({module})\n"
        f"target = getattr(module, {symbol})\n"
    )
    call_expr = call
    if "." in call.split("(", 1)[0]:
        call_expr = "target(" + call.split("(", 1)[1]
    else:
        call_expr = "target(" + call.split("(", 1)[1]
    if relation == "return_equals":
        body = (
            "try:\n"
            f"    observed = {call_expr}\n"
            "except Exception as exc:\n"
            "    print('STRICT_V5_OBSERVED_EXCEPTION:' + type(exc).__name__)\n"
            "    raise SystemExit(7)\n"
            f"expected = {expected}\n"
            "if observed != expected:\n"
            "    print('STRICT_V5_CONTRACT_MISMATCH:return_equals')\n"
            "    raise SystemExit(8)\n"
            "print('STRICT_V5_CONTRACT_SATISFIED')\n"
        )
    else:
        body = (
            "try:\n"
            f"    {call_expr}\n"
            "except Exception as exc:\n"
            f"    if type(exc).__name__ == {json.dumps(expected)}:\n"
            "        print('STRICT_V5_CONTRACT_SATISFIED')\n"
            "        raise SystemExit(0)\n"
            "    print('STRICT_V5_CONTRACT_MISMATCH:unexpected_exception:' + type(exc).__name__)\n"
            "    raise SystemExit(8)\n"
            "print('STRICT_V5_CONTRACT_MISMATCH:no_exception')\n"
            "raise SystemExit(8)\n"
        )
    source = prefix + body
    compile(source, "<strict-v5-probe>", "exec")
    return source


def docker_probe_command(probe: dict, image: str) -> list[str]:
    if not isinstance(image, str) or not image or any(char.isspace() for char in image):
        raise ValueError("invalid strict-v5 probe image")
    source = render_probe(probe)
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--workdir",
        "/testbed",
        image,
        "python",
        "-X",
        "utf8",
        "-c",
        source,
    ]


def run_probe_docker(
    probe: dict,
    image: str,
    *,
    timeout_seconds: int = 20,
    repetitions: int = 2,
) -> dict:
    command = docker_probe_command(probe, image)
    runs = []
    for _ in range(repetitions):
        try:
            completed = subprocess.run(
                command,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
            runs.append({
                "exit_code": completed.returncode,
                "stdout": completed.stdout[-2000:],
                "stderr": completed.stderr[-2000:],
                "timed_out": False,
            })
        except (OSError, subprocess.TimeoutExpired) as exc:
            stdout = exc.stdout if isinstance(exc, subprocess.TimeoutExpired) else ""
            stderr = exc.stderr if isinstance(exc, subprocess.TimeoutExpired) else str(exc)
            runs.append({
                "exit_code": None,
                "stdout": stdout[-2000:] if isinstance(stdout, str) else "",
                "stderr": stderr[-2000:] if isinstance(stderr, str) else "",
                "timed_out": isinstance(exc, subprocess.TimeoutExpired),
            })
    return _adjudicate_runs(probe, runs, network_isolated=True)


def _adjudicate_runs(probe: dict, runs: list[dict], *, network_isolated: bool) -> dict:
    signatures = [
        hashlib.sha256(
            json.dumps(run, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        for run in runs
    ]
    stable = bool(runs) and len(set(signatures)) == 1
    mismatch = bool(runs) and all(
        run["exit_code"] in {7, 8}
        and (
            "STRICT_V5_CONTRACT_MISMATCH:" in run["stdout"]
            or "STRICT_V5_OBSERVED_EXCEPTION:" in run["stdout"]
        )
        for run in runs
    )
    infrastructure_failure = not runs or any(
        run["timed_out"]
        or (
            run["exit_code"] not in {0, 7, 8}
            and "STRICT_V5_" not in run["stdout"]
        )
        for run in runs
    )
    trusted = stable and mismatch and network_isolated and not infrastructure_failure
    value = {
        "schema": "e1c-strict-v5-probe-execution-v1",
        "probe_sha256": probe["probe_sha256"],
        "runs": runs,
        "stable": stable,
        "contract_failure_observed": mismatch,
        "network_isolated": network_isolated,
        "infrastructure_failure": infrastructure_failure,
        "trusted_reproducer": trusted,
        "status": (
            "reproduced_failure"
            if trusted
            else "reproduced_failure_untrusted_executor"
            if stable and mismatch and not infrastructure_failure
            else "contract_satisfied"
            if stable and all(run["exit_code"] == 0 for run in runs)
            else "infrastructure_failure"
            if infrastructure_failure
            else "unstable_or_unclassified"
        ),
    }
    value["execution_sha256"] = audit_repair_visible_payload(value)
    return value


def run_probe(
    probe: dict,
    workspace: Path,
    *,
    timeout_seconds: int = 10,
    repetitions: int = 2,
    network_isolated: bool = False,
) -> dict:
    source = render_probe(probe)
    runs = []
    for _ in range(repetitions):
        try:
            completed = subprocess.run(
                [sys.executable, "-X", "utf8", "-c", source],
                cwd=workspace,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
            runs.append({
                "exit_code": completed.returncode,
                "stdout": completed.stdout[-2000:],
                "stderr": completed.stderr[-2000:],
                "timed_out": False,
            })
        except subprocess.TimeoutExpired as exc:
            runs.append({
                "exit_code": None,
                "stdout": (exc.stdout or "")[-2000:] if isinstance(exc.stdout, str) else "",
                "stderr": (exc.stderr or "")[-2000:] if isinstance(exc.stderr, str) else "",
                "timed_out": True,
            })
    return _adjudicate_runs(probe, runs, network_isolated=network_isolated)
