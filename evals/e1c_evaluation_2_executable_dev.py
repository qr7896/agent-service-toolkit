"""Old DEV only: import fallback plus explicit executable-probe contracts."""

from __future__ import annotations

import argparse
import asyncio
import json

from agents.model_budget import budgeted_ainvoke
from evals import e1c_evaluation_2_faithful_dev as faithful
from evals.e1c_evaluation_2_container_health import require_engine, require_valid_execution_files
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_execution_contract import parse_response

OUT = ROOT / ".codex/e1c/evaluation_2/executable-import-dev-v2"
IMPORTS = ROOT / ".codex/e1c/evaluation_2/import-prefix-old-dev-audit-v2"
PROTOCOL = ROOT / "docs/research/E1C2_EXECUTABLE_IMPORT_DEV_V2_PROTOCOL_2026-10-06.md"
runtime, dev = faithful.base.study.runtime, faithful.base.study.dev
_preflight, _messages, _execute = faithful.preflight, faithful.messages, faithful.base.study.execute_role
MODULES = ("evals/e1c_evaluation_2_executable_dev.py", "evals/e1c_evaluation_2_execution_contract.py",
           "evals/e1c_evaluation_2_import_seed_audit.py", "evals/e1c_evaluation_2_container_health.py")


def augmented(frozen, facts, imported):
    return faithful.augmented(frozen, {**facts, "terminal_production_windows": [*facts["terminal_production_windows"], *imported]})


def inputs():
    facts_proof = json.loads((faithful.FACTS / "freeze.json").read_bytes())
    imports_proof = json.loads((IMPORTS / "freeze.json").read_bytes())
    if imports_proof["module_sha256"] != _sha(ROOT / MODULES[2]):
        raise ValueError("import-only DEV audit method changed")
    for field, name in (("module_sha256", faithful.MODULES[1]), ("locator_sha256", faithful.MODULES[2])):
        if facts_proof[field] != _sha(ROOT / name):
            raise ValueError("public facts/terminal locator changed")
    rows = []
    for iid, frozen, _, workspace, image in faithful._inputs():
        facts = json.loads((faithful.FACTS / f"{iid}.json").read_bytes())
        imported = json.loads((IMPORTS / f"{iid}.json").read_bytes())
        if imported["public_statement_sha256"] != facts["statement_sha256"]:
            raise ValueError("public import origin differs from fixture facts")
        value = augmented(frozen, facts, imported["windows"])
        faithful.base.verify_workspace(value, workspace)
        path = OUT / "inputs" / f"{iid}.json"
        if path.exists() and json.loads(path.read_bytes()) != value:
            raise ValueError("executable DEV input changed")
        if not path.exists():
            _save(path, value)
        rows.append((iid, value, path, workspace, image))
    return rows


def messages(frozen, role):
    value = _messages(frozen, role)
    value[0].content += (
        '\nExecution protocol extends the JSON keys above: include "execution":'
        '{"mode":"direct_script","entrypoint":null,"fixture_source":"generated_public_issue_only"}. '
        'B must use direct_script. A may instead use mode call_entrypoint with a plain local function name: '
        'exactly one undecorated synchronous function, no parameters/annotations, imports and definition only at module scope. '
        'The controller appends that one call; keep the generated behavior check inside it. '
        'Never assume testdir/pytester injection or automatic discovery. For direct_script, actually invoke your API/check; '
        'merely defining a test function is rejected. No official test files/Gold are fixtures. '
        'Native runner/file-fixture APIs (pytest.main, runpytest, makepyfile, makeconftest) are unsupported and rejected. '
        'Abstention remains exactly {"abstain_reason":"..."} without execution.'
    )
    return value


async def guarded_invoke(model, messages, config, *, role):
    image = runtime.verified_local_image(config["configurable"]["provider_task_id"])
    require_engine((image,))
    return await budgeted_ainvoke(model, messages, config, role=role)


def execute_role(role, payload, frozen, workspace, image, root, environment):
    require_engine((image,))
    record = json.loads((root / "response.json").read_bytes())
    parsed = parse_response(record["raw"], role)
    if parsed["payload"] != payload:
        raise ValueError("compiled execution payload differs from frozen response")
    _save(root / "execution_contract.json", {"spec": parsed["execution_spec"], "response_sha256": _sha(root / "response.json"),
                                             "implicit_fixture_hydration": False})
    result = _execute(role, payload, frozen, workspace, image, root, environment)
    require_valid_execution_files(root)
    return result


def configure():
    faithful.OUT, faithful.PROTOCOL = OUT, PROTOCOL
    faithful.inputs, faithful.preflight, faithful.messages = inputs, preflight, messages
    faithful.configure()
    runtime.preflight, runtime.model_messages, runtime.execute_role = preflight, messages, execute_role
    runtime.budgeted_ainvoke = guarded_invoke
    dev.parse_response, dev.controller.parse_response = parse_response, parse_response


def preflight():
    configure()
    value = _preflight()
    configure()
    require_engine(tuple(row["image_id"] for row in value["tasks"]))
    return {**value, "schema": "e1c2-executable-import-old-dev-freeze-v2",
            "execution_modules": {name: _sha(ROOT / name) for name in MODULES},
            "execution_protocol_sha256": _sha(PROTOCOL), "import_audit_freeze_sha256": _sha(IMPORTS / "freeze.json"),
            "import_audit_result_sha256": _sha(IMPORTS / "result.json"),
            "import_files": {p.name: _sha(p) for p in sorted(IMPORTS.glob("*.json"))},
            "engine_check_before_every_request": True, "explicit_execution_manifest_required": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "gold"))
    args = parser.parse_args()
    configure()
    value = runtime.freeze() if args.command == "preflight" else asyncio.run(dev.run()) if args.command == "run" else runtime.grade()
    print(json.dumps(value, ensure_ascii=False))
