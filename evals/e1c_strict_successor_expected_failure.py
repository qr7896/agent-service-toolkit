"""Generic expected-failure contract compiler/executor for strict E1-C successor development."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from evals.e1c_strict_v7_witness_ir import WitnessIR, validate

_EXCEPTION = re.compile(r"(?m)^([A-Za-z_]\w*(?:Error|Exception)):\s*(.+?)\s*$")
_TRACEBACK_PRODUCTION_PATH = re.compile(r"site-packages/([A-Za-z0-9_./-]+\.py)")


@dataclass(frozen=True)
class FailureContract:
    exception_type: str
    message: str


@dataclass(frozen=True)
class ImportBinding:
    local_name: str
    module: str
    attribute: str | None


@dataclass(frozen=True)
class CompiledScenario:
    body_source: str
    bindings: tuple[ImportBinding, ...]
    contract: FailureContract
    candidate_path: str


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def extract_failure_contract(text: str) -> FailureContract | None:
    """Extract the last explicit public exception contract from issue-visible text."""
    matches = list(_EXCEPTION.finditer(text))
    if not matches:
        return None
    match = matches[-1]
    return FailureContract(match.group(1), " ".join(match.group(2).split()))


def extract_public_production_path(text: str) -> str | None:
    """Return the first production Python path exposed by a public traceback."""
    for match in _TRACEBACK_PRODUCTION_PATH.finditer(text.replace("\\", "/")):
        path = match.group(1).strip("/")
        parts = {part.lower() for part in path.split("/")}
        if path and not parts.intersection({"test", "tests", "testing"}):
            return path
    return None


def _valid_module(module: str) -> bool:
    return bool(module) and all(part.isidentifier() for part in module.split("."))


def compile_import_lift(
    problem_statement: str,
    source: str,
    *,
    candidate_path: str,
) -> CompiledScenario | None:
    """Lift top-level imports into deterministic importlib bindings and keep a safe body."""
    contract = extract_failure_contract(problem_statement)
    if contract is None:
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    if any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        for stmt in tree.body
        for node in ast.walk(stmt)
        if node is not stmt
    ):
        return None

    bindings: list[ImportBinding] = []
    body: list[ast.stmt] = []
    locals_seen: set[str] = set()
    for stmt in tree.body:
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                if not _valid_module(alias.name):
                    return None
                if "." in alias.name and alias.asname is None:
                    return None
                local = alias.asname or alias.name
                if not local.isidentifier() or local in locals_seen:
                    return None
                locals_seen.add(local)
                bindings.append(ImportBinding(local, alias.name, None))
            continue
        if isinstance(stmt, ast.ImportFrom):
            if stmt.level != 0 or not stmt.module or not _valid_module(stmt.module):
                return None
            for alias in stmt.names:
                if alias.name == "*" or not alias.name.isidentifier():
                    return None
                local = alias.asname or alias.name
                if not local.isidentifier() or local in locals_seen:
                    return None
                locals_seen.add(local)
                bindings.append(ImportBinding(local, stmt.module, alias.name))
            continue
        body.append(stmt)

    if not bindings or not body:
        return None
    body_source = ast.unparse(ast.Module(body=body, type_ignores=[])).strip() + "\n"
    witness = WitnessIR(
        kind="python_scenario",
        source=body_source,
        observable="expected_public_exception",
        candidate_path=candidate_path,
        provenance="public_issue_expected_failure_plus_import_lift",
        benchmark_assertion_used=False,
        task_id_used=False,
    )
    safe, _ = validate(witness)
    if not safe:
        return None
    return CompiledScenario(body_source, tuple(bindings), contract, candidate_path)


def render_compiled(compiled: CompiledScenario) -> str:
    lines = ["import importlib"]
    for binding in compiled.bindings:
        module = json.dumps(binding.module)
        if binding.attribute is None:
            lines.append(f"{binding.local_name} = importlib.import_module({module})")
        else:
            attribute = json.dumps(binding.attribute)
            lines.append(
                f"{binding.local_name} = getattr(importlib.import_module({module}), {attribute})"
            )
    lines.append(compiled.body_source.rstrip())
    rendered = "\n".join(lines) + "\n"
    compile(rendered, "<strict-successor-expected-failure>", "exec")
    return rendered


def classify_failure(
    expected: FailureContract, stderr: str, returncode: int | None
) -> tuple[bool, str, FailureContract | None]:
    observed = extract_failure_contract(stderr)
    if returncode is None:
        return False, "not_executed", observed
    if returncode == 0:
        return False, "semantic_failure_not_reproduced", observed
    if observed is None:
        return False, "nonzero_without_exception_contract", None
    if observed.exception_type != expected.exception_type:
        return False, "exception_type_mismatch", observed
    if observed.message != expected.message:
        return False, "exception_message_mismatch", observed
    return True, "trusted_expected_failure_reproduced", observed


def run_expected_failure_preflight(
    compiled: CompiledScenario,
    *,
    source_root: Path,
    expected_base_commit: str,
    image_digest: str,
    artifact_path: Path,
    timeout_seconds: int = 60,
) -> dict:
    if timeout_seconds < 1 or timeout_seconds > 120:
        raise ValueError("preflight timeout must be within 1..120 seconds")
    head = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    observed_base_commit = head.stdout.strip() if head.returncode == 0 else ""
    rendered = render_compiled(compiled)
    command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--workdir",
        "/testbed",
        image_digest,
        "python",
        "-X",
        "utf8",
        "-c",
        rendered,
    ]
    timed_out = False
    returncode = None
    stdout = ""
    stderr = ""
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")

    matched, reason, observed = classify_failure(compiled.contract, stderr, returncode)
    exact_base = bool(expected_base_commit) and expected_base_commit == observed_base_commit
    immutable_image = "@sha256:" in image_digest
    network_disabled = "--network" in command and command[command.index("--network") + 1] == "none"
    trusted = all((not timed_out, exact_base, immutable_image, network_disabled, matched))
    value = {
        "schema": "e1c-strict-successor-expected-failure-preflight-v1",
        "provider_calls": 0,
        "candidate_path": compiled.candidate_path,
        "compiled_body_sha256": _sha_text(compiled.body_source),
        "binding_count": len(compiled.bindings),
        "bindings": [asdict(binding) for binding in compiled.bindings],
        "expected_contract": asdict(compiled.contract),
        "observed_contract": asdict(observed) if observed else None,
        "expected_base_commit": expected_base_commit,
        "observed_base_commit": observed_base_commit,
        "image_digest": image_digest,
        "exact_base_identity": exact_base,
        "immutable_image_identity": immutable_image,
        "network_disabled": network_disabled,
        "executed": returncode is not None and not timed_out,
        "timed_out": timed_out,
        "returncode": returncode,
        "stdout_sha256": _sha_text(stdout),
        "stderr_sha256": _sha_text(stderr),
        "trusted_reproducer": trusted,
        "classification": reason if not trusted else "trusted_expected_failure_reproduced",
        "timeout_seconds": timeout_seconds,
    }
    value["preflight_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(payload, encoding="utf-8")
    value["artifact_file_sha256"] = _sha_text(payload)
    return value
