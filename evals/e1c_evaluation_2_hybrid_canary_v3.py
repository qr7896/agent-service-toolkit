"""Frozen hybrid-v2 independent canary; metadata proxy only, image bytes direct."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import subprocess
import urllib.request

from evals import e1c_evaluation_2_canary_select as selector
from evals import e1c_evaluation_2_canary_v2_stage as stage
from evals import e1c_evaluation_2_hybrid_controller_v2 as controller
from evals import e1c_evaluation_2_production_coverage as coverage
from evals.e1c_evaluation_2_canary_v2_metadata_proxy import IMAGE, MetadataClient
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

FREEZE = ROOT / "data/e1c_evaluation_2_hybrid_canary_v3_method_freeze.json"
IDENTITY = ROOT / "data/e1c_evaluation_2_hybrid_canary_v3_identity.json"
GATE = ROOT / "data/e1c_evaluation_2_hybrid_controller_v2_dev_gate.json"
PROTOCOL = ROOT / "docs/research/E1C2_HYBRID_CANARY_V3_METHOD_2026-10-05.md"
OUT = ROOT / ".codex/e1c/evaluation_2/hybrid-canary-v3"
SALT = "e1c2-source-contract-hybrid-canary-v3-2026-10-05"
METHOD_FILES = (
    "evals/e1c_evaluation_2_hybrid_canary_v3.py",
    "evals/e1c_evaluation_2_hybrid_controller_v2.py",
    "evals/e1c_evaluation_2_fallback_oracle.py",
    "evals/e1c_evaluation_2_hybrid_dev.py",
    "evals/e1c_evaluation_2_source_contract.py",
    "evals/e1c_evaluation_2_raw_json.py",
    "evals/e1c_evaluation_2_production_coverage.py",
    "evals/e1c_evaluation_2_contract_ab_dev.py",
    "evals/e1c_evaluation_2_contract_ab_dev_v2.py",
    "evals/e1c_evaluation_2_contract_method.py",
    "evals/e1c_evaluation_2_pregrader_policy.py",
    "evals/e1c_evaluation_2_canary_v2_metadata_proxy.py",
    "evals/e1c_evaluation_2_canary_v2_stage.py",
    "evals/e1c_evaluation_2_canary_metadata.py",
    "evals/e1c_evaluation_2_canary_transport.py",
    "evals/e1c_evaluation_2_canary_acquire.py",
    "evals/e1c_evaluation_2_canary_materialize.py",
    "evals/e1c_evaluation_2_admission.py",
    "evals/e1c_evaluation_2_mirror_acquire.py",
    "evals/e1c_evaluation_2_image_transport.py",
    "evals/e1c_evaluation_2_batch_acquire.py",
    "evals/e1c_evaluation_2_unified_dev_v2_gold.py",
    "evals/e1c_evaluation_2_unified_dev_v4.py",
    "evals/e1c_strict_v5_official_metadata.py",
    "src/agents/model_budget.py",
    "src/agents/model_router.py",
    "docs/research/E1C2_HYBRID_CONTROLLER_V2_METHOD_2026-10-05.md",
    "docs/research/E1C2_HYBRID_CANARY_V3_METHOD_2026-10-05.md",
)


def method() -> dict:
    selector._checked_inputs()
    gate = json.loads(GATE.read_bytes())
    if (gate.get("controller_development_gate_pass") is not True
            or gate.get("independent_validation") is not False
            or gate.get("trusted_reproducer_after_semantic_audit", 0) < 2
            or gate.get("repository_count", 0) < 2):
        raise ValueError("development evidence gate is missing; not independent confirmation")
    original = json.loads((ROOT / "data/e1c_evaluation_2_canary_v2_method_freeze.json").read_bytes())
    files = {**original["method_files"], **{name: _sha(ROOT / name) for name in METHOD_FILES}}
    if any(_sha(ROOT / name) != digest for name, digest in original["method_files"].items()):
        raise ValueError("historical canary method changed")
    return {"schema": "e1c2-hybrid-canary-v3-method-freeze-v1",
            "status": "method_frozen_before_canary_selection", "method_files": files,
            "dev_gate_sha256": _sha(GATE), "model": "deepseek-flash", "thinking": "disabled",
            "temperature": 0, "sdk_retries": 0, "max_requests": 6, "max_requests_per_task": 2,
            "max_output_tokens_per_request": 3000, "per_task_provider_token_cap": 20000,
            "batch_provider_token_cap": 60000, "candidate_count": 3, "minimum_trusted": 2,
            "selection_salt": SALT, "provider_calls": 0, "canary_task_content_inspected": False}


def freeze_method() -> dict:
    if IDENTITY.exists():
        raise FileExistsError("identity already sealed; no method refreeze")
    value = method()
    if FREEZE.exists():
        if json.loads(FREEZE.read_bytes()) != value:
            raise ValueError("method freeze differs")
    else:
        _save(FREEZE, value)
    return value


def checked_method() -> dict:
    value = method()
    if json.loads(FREEZE.read_bytes()) != value:
        raise ValueError("frozen method bytes changed")
    return value


def select_identity() -> dict:
    checked_method()
    # Reuse the fixed metadata-only selector; include its original canary explicitly.
    prior = selector.FREEZE, selector.IDENTITY, selector.SALT, selector.method
    selector.FREEZE, selector.IDENTITY, selector.SALT, selector.method = FREEZE, IDENTITY, SALT, method
    try:
        return selector.freeze_identity()
    finally:
        selector.FREEZE, selector.IDENTITY, selector.SALT, selector.method = prior


def bind_stages() -> None:
    checked_method()
    stage.FREEZE, stage.IDENTITY, stage.OUT, stage.method = FREEZE, IDENTITY, OUT, method
    stage.METADATA, stage.TRANSPORT = OUT / "metadata.json", OUT / "image_transport.json"
    stage.ACQUIRE, stage.GRADER = OUT / "acquire", OUT / "grader-only"
    stage.PUBLIC, stage.SOURCE = OUT / "issue-only", OUT / "source"
    stage.bind()


def audit_transport() -> dict:
    metadata = json.loads(stage.METADATA.read_bytes())
    identity = json.loads(IDENTITY.read_bytes())
    if (metadata.get("identity_sha256") != _sha(IDENTITY)
            or [t["instance_id"] for t in metadata["tasks"]] != [t["instance_id"] for t in identity["tasks"]]):
        raise ValueError("official task metadata identity differs")
    if stage.TRANSPORT.exists():
        value = json.loads(stage.TRANSPORT.read_bytes())
        if (value.get("identity_sha256") != _sha(IDENTITY)
                or value.get("metadata_sha256") != _sha(stage.METADATA)
                or value.get("method_freeze_sha256") != _sha(FREEZE)):
            raise ValueError("cached metadata seal binding differs")
        return value
    client, rows = MetadataClient(), []
    for task in metadata["tasks"]:
        match = IMAGE.fullmatch(task["image"])
        if not match:
            raise ValueError("unexpected official image reference")
        repository = "swebench/" + match.group(1)
        official = client.manifest(repository, official=True)
        mirror = client.manifest(repository, official=False)
        if official != mirror:
            raise ValueError("official and direct mirror descriptors differ")
        rows.append({"instance_id": task["instance_id"], "official_image": task["image"],
                     "repository": repository, "official": official, "mirror": mirror, "digest_identical": True})
        print(json.dumps({"instance_id": task["instance_id"], "compressed_gib": round(official["compressed_layer_bytes"] / 1024**3, 3)}), flush=True)
    value = {"schema": "e1c2-canary-image-transport-v3", "identity_sha256": _sha(IDENTITY),
             "metadata_sha256": _sha(stage.METADATA), "method_freeze_sha256": _sha(FREEZE),
             "mirror_host": "docker.1panel.live", "official_proxy_metadata_only": True,
             "official_bytes": client.official_bytes, "official_requests": client.official_requests,
             "mirror_os_proxy_bypassed": True, "blob_requests": 0, "provider_calls": 0, "rows": rows}
    _save(stage.TRANSPORT, value)
    return value


def prepare_public() -> list[dict]:
    rows = stage.public()
    for row in rows:
        iid = row["instance_id"]
        seed_path = stage.PUBLIC / iid / "frozen_input_v4.json"
        if not seed_path.is_file():
            continue
        value = coverage.freeze_input(json.loads(seed_path.read_bytes()), stage.SOURCE / iid)
        path = stage.PUBLIC / iid / "frozen_input_hybrid_v1.json"
        if path.exists():
            if json.loads(path.read_bytes()) != value:
                raise ValueError("frozen production coverage differs")
        else:
            _save(path, value)
    return rows


def live_inputs():
    rows = []
    for task in stage.materialize.rows():
        iid = task["instance_id"]
        phases = [stage.GRADER / iid / f"{phase}.json" for phase in ("base", "gold")]
        if not all(p.is_file() and json.loads(p.read_bytes()).get("phase_pass") is True for p in phases):
            continue
        path = stage.PUBLIC / iid / "frozen_input_hybrid_v1.json"
        frozen, workspace = json.loads(path.read_bytes()), stage.SOURCE / iid
        head = subprocess.check_output(["git", "-C", str(workspace), "rev-parse", "HEAD"], text=True, timeout=30).strip()
        dirty = subprocess.check_output(["git", "-C", str(workspace), "status", "--porcelain", "--untracked-files=all"], text=True, timeout=90).strip()
        if head != frozen["base_commit"] or dirty:
            raise ValueError("canary production source is not clean at its frozen base")
        if coverage.freeze_input(json.loads((stage.PUBLIC / iid / "frozen_input_v4.json").read_bytes()), workspace) != frozen:
            raise ValueError("canary production input changed")
        rows.append((iid, frozen, path, workspace, stage.materialize.verified_image(iid)))
    if not rows:
        raise ValueError("no officially dual-admitted task; do not start provider")
    return rows


def bind_live() -> None:
    bind_stages()
    controller.OUT, controller.PROTOCOL = OUT / "live", PROTOCOL
    controller.configure()
    runtime = controller.runtime
    runtime.IDENTITY, runtime.FIXED_DENOMINATOR = IDENTITY, 3
    runtime.TASK_CAP, runtime.BATCH_CAP, runtime.OUTPUT_CAP = 20000, 60000, 3000
    runtime.inputs, runtime.preflight = live_inputs, live_preflight


def live_preflight() -> dict:
    bind_live()
    value = controller.preflight()
    controller.runtime.preflight = live_preflight
    value.update({"canary_method_freeze_sha256": _sha(FREEZE),
                  "metadata_sha256": _sha(stage.METADATA), "transport_sha256": _sha(stage.TRANSPORT),
                  "cohort": [t["instance_id"] for t in json.loads(IDENTITY.read_bytes())["tasks"]]})
    return value


def grade() -> dict:
    from evals import e1c_evaluation_2_unified_dev_v2_gold as gold

    importlib.import_module("evals.e1c_evaluation_2_unified_dev_v4")
    bind_live()
    gold.base.OUT, gold.base.FREEZE, gold.base.preflight = OUT / "live", OUT / "live/freeze.json", live_preflight
    gold.GRADER, gold.OUT = stage.GRADER, stage.GRADER / "hybrid-discrimination"
    gold.materialize, gold.verified_local_image = stage.admission.materialize, stage.materialize.verified_image
    return gold.run()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze-method", "select", "metadata", "transport", "download", "admit", "public", "preflight", "run", "gold"))
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--timeout-per-image", type=int, default=21600)
    args = parser.parse_args()
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    if args.command == "freeze-method":
        value = freeze_method()
    elif args.command == "select":
        value = select_identity()
    else:
        bind_stages()
        if args.command == "metadata":
            value = stage.metadata.acquire()
        elif args.command == "transport":
            value = audit_transport()
        elif args.command == "download":
            audit_transport()
            value = stage.acquire.acquire(timeout_per_image=args.timeout_per_image)
        elif args.command == "admit":
            value = stage.admit(args.timeout)
        elif args.command == "public":
            value = prepare_public()
        else:
            bind_live()
            value = controller.runtime.freeze() if args.command == "preflight" else asyncio.run(controller.runtime.run()) if args.command == "run" else grade()
    print(json.dumps(value, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
