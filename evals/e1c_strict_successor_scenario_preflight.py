"""Fail-closed zero-provider preflight for already-frozen strict Python-scenario witnesses."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from evals.e1c_strict_v7_witness_ir import WitnessIR, validate


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def persist(value: dict, path) -> str:
    """Persist one canonical preflight artifact and return its file SHA-256."""
    from pathlib import Path

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    target.write_text(payload, encoding="utf-8")
    return hashlib.sha256(payload.encode()).hexdigest()


def assess(
    witness: dict,
    *,
    expected_base_commit: str,
    observed_base_commit: str,
    image_digest: str,
    command: list[str],
    returncode: int | None,
    timed_out: bool,
    stdout_sha256: str,
    stderr_sha256: str,
) -> dict:
    """Return auditable promotion evidence; never executes or repairs a witness."""
    required = {"kind", "source", "observable", "candidate_path"}
    if not required <= witness.keys():
        raise ValueError("incomplete frozen witness")
    ir = WitnessIR(
        kind=str(witness["kind"]),
        source=str(witness["source"]),
        observable=str(witness["observable"]),
        candidate_path=str(witness["candidate_path"]),
        provenance=str(witness.get("provenance", "projected_issue_plus_production_localization")),
        benchmark_assertion_used=bool(witness.get("benchmark_assertion_used", False)),
        task_id_used=bool(witness.get("task_id_used", False)),
    )
    safe, reason = validate(ir)
    network_disabled = "--network" in command and command[command.index("--network") + 1] == "none"
    exact_base = bool(expected_base_commit) and expected_base_commit == observed_base_commit
    immutable_image = "@sha256:" in image_digest
    scenario = ir.kind == "python_scenario"
    observable_ok = ir.observable.strip() == "scenario_exit_code == 0"
    executed = returncode is not None and not timed_out
    passed = executed and returncode == 0
    promoted = all((safe, scenario, observable_ok, network_disabled, exact_base, immutable_image, passed))
    value = {
        "schema": "e1c-strict-successor-scenario-preflight-v1",
        "provider_calls": 0,
        "witness_sha256": str(witness.get("witness_sha256", "")),
        "candidate_path": ir.candidate_path,
        "observable": ir.observable,
        "expected_base_commit": expected_base_commit,
        "observed_base_commit": observed_base_commit,
        "image_digest": image_digest,
        "command": list(command),
        "safe_typed_witness": safe,
        "witness_validation_reason": reason,
        "scenario_kind": scenario,
        "observable_supported": observable_ok,
        "network_disabled": network_disabled,
        "exact_base_identity": exact_base,
        "immutable_image_identity": immutable_image,
        "executed": executed,
        "timed_out": bool(timed_out),
        "returncode": returncode,
        "stdout_sha256": stdout_sha256,
        "stderr_sha256": stderr_sha256,
        "execution_ready": promoted,
        "promotion_reason": "preflight_pass" if promoted else "fail_closed",
    }
    value["preflight_sha256"] = _sha(value)
    return value
