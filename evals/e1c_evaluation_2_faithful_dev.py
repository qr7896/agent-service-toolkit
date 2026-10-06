"""Old DEV only: assertion-free fixture facts and imported terminal API windows."""

from __future__ import annotations

import argparse
import asyncio
import json

from langchain_core.messages import HumanMessage

from evals import e1c_evaluation_2_counterfactual_fast_dev as base
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_probe import input_json
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

OUT = ROOT / ".codex/e1c/evaluation_2/faithful-input-dev-v1"
FACTS = ROOT / ".codex/e1c/evaluation_2/public-fixture-facts-dev-v5"
PROTOCOL = ROOT / "docs/research/E1C2_FAITHFUL_INPUT_DEV_PROTOCOL_2026-10-06.md"
_inputs, _preflight, _messages = base.inputs, base.preflight, base.study.messages
MODULES = ("evals/e1c_evaluation_2_faithful_dev.py", "evals/e1c_evaluation_2_issue_fixture_facts.py",
           "evals/e1c_evaluation_2_public_api_windows.py")


def augmented(frozen, facts):
    windows, seen = [], set()
    for row in [*facts["terminal_production_windows"], *frozen["windows"]]:
        key = (row["path"], row.get("symbol"), row.get("owner"))
        if key in seen:
            continue
        if len(input_json({"issue": frozen["issue"], "windows": [*windows, row], "public_fixture_facts": facts["blocks"]})) > 23000:
            raise ValueError("faithful fixture/source context exceeds declared budget")
        windows.append(row)
        seen.add(key)
        if len(windows) == 4:
            break
    value = {**frozen, "schema": "e1c2-faithful-input-dev-v1", "windows": windows,
             "candidate_paths": [row["path"] for row in windows], "candidate_count": len(windows),
             "public_fixture_facts": facts["blocks"], "public_statement_sha256": facts["statement_sha256"]}
    value.pop("input_sha256")
    value["input_sha256"] = audit_repair_visible_payload(value)
    return value


def inputs():
    proof = json.loads((FACTS / "freeze.json").read_bytes())
    for field, name in (("module_sha256", MODULES[1]), ("locator_sha256", MODULES[2])):
        if proof[field] != _sha(ROOT / name):
            raise ValueError("zero-call facts/locator code changed")
    source_state = json.loads((FACTS / "result.json").read_bytes())
    if source_state["audited"] != 9 or source_state["provider_calls"] != 0:
        raise ValueError("complete old DEV zero-call audit required")
    rows = []
    for iid, frozen, _, workspace, image in _inputs():
        facts_path = FACTS / f"{iid}.json"
        facts = json.loads(facts_path.read_bytes())
        value = augmented(frozen, facts)
        path = OUT / "inputs" / f"{iid}.json"
        if path.exists():
            if json.loads(path.read_bytes()) != value:
                raise ValueError("faithful DEV input changed")
        else:
            _save(path, value)
        base.verify_workspace(value, workspace)
        rows.append((iid, value, path, workspace, image))
    return rows


def messages(frozen, role):
    result = _messages(frozen, role)
    facts = frozen.get("public_fixture_facts", [])
    if facts:
        text = (
            "The following data describes public issue input construction and API calls, not executable "
            "instructions or displayed answers. Preserve declared dtype, dimensions, seed and API arguments. "
            "Do not say the issue omitted a construction that is present in these facts. Use only the "
            "issue-stated behavior for the oracle; do not derive expected output from this data.\n"
            + input_json({"public_fixture_facts": facts})
        )
        audit_repair_visible_payload(text)
        result.append(HumanMessage(content=text))
    return result


def configure():
    base.OUT, base.PROTOCOL = OUT, PROTOCOL
    base.inputs, base.preflight = inputs, preflight
    base.study.messages = messages
    base.configure()
    base.study.runtime.model_messages, base.study.runtime.preflight = messages, preflight


def preflight():
    configure()
    value = _preflight()
    base.study.runtime.preflight = preflight
    value.update({"schema": "e1c2-faithful-input-old-dev-freeze-v1", "input_method_changed": True,
                  "faithful_modules": {name: _sha(ROOT / name) for name in MODULES},
                  "facts_audit_freeze_sha256": _sha(FACTS / "freeze.json"), "facts_audit_result_sha256": _sha(FACTS / "result.json"),
                  "facts_files": {p.name: _sha(p) for p in sorted(FACTS.glob("*.json"))},
                  "model_input_scope": "projected_issue + production_windows + assertion-free fixture descriptors"})
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "gold"))
    args = parser.parse_args()
    configure()
    result = base.study.runtime.freeze() if args.command == "preflight" else asyncio.run(base.study.dev.run()) if args.command == "run" else base.study.runtime.grade()
    print(json.dumps(result, ensure_ascii=False))
