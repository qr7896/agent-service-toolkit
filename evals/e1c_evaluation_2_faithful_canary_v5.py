"""Faithful independent canary; reuse sealed plumbing, check engine before each request."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import urllib.request

from agents.model_budget import budgeted_ainvoke
from evals import e1c_evaluation_2_counterfactual_canary_v4 as runner
from evals import e1c_evaluation_2_faithful_dev as faithful
from evals.e1c_evaluation_2_container_health import require_engine, require_valid_execution_files
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_issue_fixture_facts import extract_facts
from evals.e1c_evaluation_2_public_api_windows import terminal_windows

frame, runtime = runner.frame, runner.runtime
OUT = ROOT / ".codex/e1c/evaluation_2/faithful-canary-v5"
FREEZE = ROOT / "data/e1c_evaluation_2_faithful_canary_v5_method_freeze.json"
IDENTITY = ROOT / "data/e1c_evaluation_2_faithful_canary_v5_identity.json"
GATE = ROOT / "data/e1c_evaluation_2_faithful_replay_dev_gate.json"
PROTOCOL = ROOT / "docs/research/E1C2_FAITHFUL_CANARY_V5_METHOD_2026-10-06.md"
_method, _preflight = frame.method, runtime.preflight
FILES = (*runner.FILES, "evals/e1c_evaluation_2_faithful_canary_v5.py",
         "evals/e1c_evaluation_2_faithful_dev.py", "evals/e1c_evaluation_2_issue_fixture_facts.py",
         "evals/e1c_evaluation_2_public_api_windows.py", "evals/e1c_evaluation_2_container_health.py",
         "evals/e1c_blind_boundary.py",
         "docs/research/E1C2_FAITHFUL_INPUT_DEV_PROTOCOL_2026-10-06.md",
         "docs/research/E1C2_FAITHFUL_CANARY_V5_METHOD_2026-10-06.md")


def method():
    value = _method()
    gate = json.loads(GATE.read_bytes())
    if gate.get("reference_four_retained") is not True or gate.get("gold_discriminating", 0) < 5:
        raise ValueError("faithful DEV evidence gate not met")
    return {**value, "schema": "e1c2-faithful-canary-v5-method-freeze",
            "dev_evidence_scope": "old DEV cache replay plus human observable-behavior review; not automatic semantic proof",
            "engine_check_before_every_request": True,
            "method_files": {**value["method_files"], **{name: _sha(ROOT / name) for name in FILES}}}


def configure():
    frame.OUT, frame.FREEZE, frame.IDENTITY, frame.PROTOCOL, frame.GATE = OUT, FREEZE, IDENTITY, PROTOCOL, GATE
    frame.SALT = "e1c2-faithful-independent-canary-v5-2026-10-06"
    frame.method, frame.live_preflight, frame.live_inputs = method, live_preflight, inputs
    runner.OUT = OUT  # Existing runner's budget/STOP/state handling, in a new namespace.


def augment_seed(seed, workspace, statement):
    facts = extract_facts(statement)
    facts["terminal_production_windows"] = terminal_windows(facts, workspace)
    return faithful.augmented(runner.cf.dev.path_input(seed, workspace), facts), facts


def public():
    rows = frame.stage.public()
    for row in rows:
        if row.get("status") == "fixed_denominator_official_admission_failed":
            continue
        iid = row["instance_id"]
        folder, workspace = frame.stage.PUBLIC / iid, frame.stage.SOURCE / iid
        raw = (folder / "problem_statement.md").read_bytes()
        blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        if blob != row["issue_blob_sha"]:
            raise ValueError("public statement differs from verified official blob")
        seed_path = folder / "frozen_input_v4.json"
        seed = json.loads(seed_path.read_bytes())
        value, facts = augment_seed(seed, workspace, raw.decode("utf-8"))
        value["seed_input_sha256"] = _sha(seed_path)
        path = folder / "frozen_input_counterfactual_v1.json"
        if path.exists() and json.loads(path.read_bytes()) != value:
            raise ValueError("faithful canary public input changed")
        if not path.exists():
            _save(path, value)
            _save(folder / "public_fixture_facts.json", {**facts, "official_issue_blob_sha": blob})
    return rows


def inputs():
    rows = runner.inputs()
    for iid, frozen, _, workspace, _ in rows:
        folder = frame.stage.PUBLIC / iid
        raw = (folder / "problem_statement.md").read_bytes()
        facts = json.loads((folder / "public_fixture_facts.json").read_bytes())
        if hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest() != facts["official_issue_blob_sha"]:
            raise ValueError("canary public input origin changed")
        seed_path = folder / "frozen_input_v4.json"
        actual, _ = augment_seed(json.loads(seed_path.read_bytes()), workspace, raw.decode("utf-8"))
        actual["seed_input_sha256"] = _sha(seed_path)
        if actual != frozen:
            raise ValueError("canary facts/production windows changed")
    return rows


async def guarded_invoke(model, messages, config, *, role):
    image = frame.stage.materialize.verified_image(config["configurable"]["provider_task_id"])
    require_engine((image,))
    return await budgeted_ainvoke(model, messages, config, role=role)


def guarded_execute(role, payload, frozen, workspace, image, root, environment):
    require_engine((image,))
    result = runner.cf.execute_role(role, payload, frozen, workspace, image, root, environment)
    require_valid_execution_files(root)
    return result


def bind_live():
    frame.bind_live()
    runtime.inputs, runtime.preflight = inputs, live_preflight
    runtime.execute_role, runtime.model_messages = guarded_execute, faithful.messages
    runtime.budgeted_ainvoke = guarded_invoke


def live_preflight():
    bind_live()
    value = _preflight()
    require_engine(tuple(row["image_id"] for row in value["tasks"]))
    return {**value, "schema": "e1c2-faithful-canary-v5-live-freeze",
            "canary_method_freeze_sha256": _sha(FREEZE), "metadata_sha256": _sha(frame.stage.METADATA),
            "transport_sha256": _sha(frame.stage.TRANSPORT),
            "cohort": [t["instance_id"] for t in json.loads(IDENTITY.read_bytes())["tasks"]],
            "engine_check_before_every_request": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze-method", "select", "metadata", "transport", "download", "admit", "public", "preflight", "run", "gold"))
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--timeout-per-image", type=int, default=21600)
    args = parser.parse_args()
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    configure()
    if args.command in {"freeze-method", "select"}:
        result = frame.freeze_method() if args.command == "freeze-method" else frame.select_identity()
    else:
        frame.bind_stages()
        if args.command == "metadata":
            result = frame.stage.metadata.acquire()
        elif args.command == "transport":
            result = frame.audit_transport()
        elif args.command == "download":
            frame.audit_transport()
            result = frame.stage.acquire.acquire(timeout_per_image=args.timeout_per_image)
        elif args.command == "admit":
            require_engine()
            result = frame.stage.admit(args.timeout)
        elif args.command == "public":
            result = public()
        else:
            bind_live()
            result = runtime.freeze() if args.command == "preflight" else asyncio.run(runner.run()) if args.command == "run" else frame.grade()
    print(json.dumps(result, ensure_ascii=False))
