"""Fresh old DEV: controller grammar and explicit, separated output instructions."""

from __future__ import annotations

import argparse
import asyncio
import json

from langchain_core.messages import HumanMessage, SystemMessage

from evals import e1c_evaluation_2_executable_dev as study
from evals.e1c_evaluation_2_controller_manifest import parse_response
from evals.e1c_evaluation_2_dev_pilot import ROOT, _sha
from evals.e1c_evaluation_2_probe import input_json

OUT = ROOT / ".codex/e1c/evaluation_2/controller-generation-old-dev-v4"
PROTOCOL = ROOT / "docs/research/E1C2_CONTROLLER_GENERATION_DEV_V4_PROTOCOL_2026-10-06.md"
runtime = study.runtime
_preflight, _messages = study.preflight, study._messages
MODULES = (*study.MODULES, "evals/e1c_evaluation_2_controller_manifest.py",
           "evals/e1c_evaluation_2_controller_generation_dev.py")


def messages(frozen, role):
    value = _messages(frozen, role)
    if role == "A":
        from evals.e1c_evaluation_2_unified_dev_v4 import prompt

        context = input_json({"issue": frozen["issue"], "windows": frozen["windows"]})
        original = prompt(frozen)
        if not original.endswith(context):
            raise ValueError("trusted A instructions cannot be separated from public input")
        value = [SystemMessage(content=original[:-len(context)].strip()), HumanMessage(content=context), *value[1:]]
    value[0].content += (
        " Controller owns execution metadata. Do not emit execution, issue, windows or other input echoes. "
        "Native runner/file-fixture APIs are unsupported; no pytest.main/runpytest/makepyfile/makeconftest. "
        "A may use a directly invoked script or a unique ordinary zero-parameter function with its check; "
        "the controller can append that one call. Do not require injected testdir/pytester."
    )
    fields = '{"source":"standalone generated Python"}' if role == "A" else (
        "seven strings: issue_quote, expected_quote, oracle, setup_source, control_action, target_action, assertion")
    value.append(HumanMessage(content=(
        "Now generate a new issue-grounded executable probe; do not repeat the supplied data. "
        f"Return only JSON with {fields}, or exactly {{\"abstain_reason\":\"reason\"}}. "
        "No execution metadata, markdown or input issue/windows keys. Do not guess an unstated expected value."
    )))
    return value


def configure():
    study.OUT, study.PROTOCOL, study.MODULES = OUT, PROTOCOL, MODULES
    study.messages, study.parse_response, study.preflight = messages, parse_response, preflight
    study.configure()


def preflight():
    configure()
    value = _preflight()
    configure()
    return {**value, "schema": "e1c2-controller-generation-old-dev-freeze-v4",
            "explicit_execution_manifest_required": False, "controller_derived_execution_manifest": True,
            "source_input_method_changed": False, "fresh_model_generation": True,
            "controller_prompt_protocol_sha256": _sha(PROTOCOL)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "gold"))
    args = parser.parse_args()
    configure()
    value = runtime.freeze() if args.command == "preflight" else asyncio.run(study.dev.run()) if args.command == "run" else runtime.grade()
    print(json.dumps(value, ensure_ascii=False))
