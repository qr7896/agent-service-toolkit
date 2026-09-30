"""Assemble strict-v5 post-freeze zero-provider admission evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_admission import AdmissionRow, evaluate
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

MANIFEST = ROOT / "data" / "e1c_strict_v5_canary_manifest.json"
IDENTITY = ROOT / "data" / "e1c_strict_v5_postfreeze_identity.json"
ROOT_MATERIALIZED = ROOT / ".codex" / "e1c" / "strict-v5" / "materialized-v1"
OUT = ROOT / "data" / "e1c_strict_v5_canary_admission.json"


def _load_optional(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _projection_status(instance_id: str) -> tuple[str, bool]:
    path = ROOT_MATERIALIZED / instance_id / "projection.json"
    payload = _load_optional(path)
    status = str(payload.get("status", "missing"))
    if status == "missing" and path.is_file():
        status = "projected"
    return status, bool(payload)


def _image_ready(image: dict, verification: dict) -> bool:
    return bool(image.get("ready")) or bool(verification.get("image_digest"))


def build(output: Path = OUT) -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    identity = _load_optional(IDENTITY)
    identity_rows = {
        row.get("instance_id"): row
        for row in identity.get("rows", [])
        if isinstance(row, dict)
    }
    admission_rows = []
    evidence_rows = []
    for task in manifest["tasks"]:
        instance_id = task["instance_id"]
        ident = identity_rows.get(instance_id, {})
        projection_status, projection_present = _projection_status(instance_id)
        runtime = _load_optional(ROOT_MATERIALIZED / instance_id / "runtime.json")
        verification = _load_optional(ROOT_MATERIALIZED / instance_id / "verification.json")
        probe = _load_optional(ROOT_MATERIALIZED / instance_id / "probe_execution.json")
        probe_plan = runtime.get("probe_plan", {}) if isinstance(runtime, dict) else {}
        probe_status = probe.get("status") or probe_plan.get("status") or "missing"
        repair_visible = {
            "instance_id": instance_id,
            "projection": _load_optional(ROOT_MATERIALIZED / instance_id / "projection.json"),
            "runtime": runtime,
            "probe": probe,
        }
        leakage_free = True
        leakage_reason = None
        try:
            audit_repair_visible_payload(repair_visible)
        except Exception as exc:
            leakage_free = False
            leakage_reason = f"{type(exc).__name__}: {exc}"
        source = ident.get("source", {})
        image = ident.get("image_identity", {})
        image_ready = _image_ready(image, verification)
        row = AdmissionRow(
            instance_id=instance_id,
            identity_frozen=True,
            projection_status=projection_status,
            source_commit_matches=bool(source.get("ready"))
            and source.get("head") == task["base_commit"],
            image_present=image_ready,
            base_fail=verification.get("base_fail") is True,
            gold_pass=verification.get("gold_pass") is True,
            trusted_reproducer=probe.get("trusted_reproducer") is True,
            leakage_free=leakage_free,
            infrastructure_ok=(
                bool(source.get("ready"))
                and image_ready
                and verification.get("infrastructure_failure") is not True
                and probe.get("infrastructure_failure") is not True
            ),
        )
        admission_rows.append(row)
        evidence_rows.append({
            "instance_id": instance_id,
            "projection_present": projection_present,
            "source_status": source.get("status", "missing"),
            "image_status": (
                image.get("status", "missing")
                if image.get("ready")
                else "verification_image_digest"
                if verification.get("image_digest")
                else image.get("status", "missing")
            ),
            "verification_status": verification.get("status", "missing"),
            "probe_status": probe_status,
            "leakage_free": leakage_free,
            "leakage_reason": leakage_reason,
        })
    result = evaluate(admission_rows)
    result["evidence_rows"] = evidence_rows
    result["provider_calls"] = 0
    result["live_model_run"] = False
    result["frozen_instance_ids"] = [row["instance_id"] for row in manifest["tasks"]]
    result["report_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
