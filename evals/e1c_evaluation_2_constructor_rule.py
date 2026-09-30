"""Zero-provider, public-issue-only probe for Boolean constructor requests."""

from __future__ import annotations

import argparse
import hashlib
import json
import re

from evals.e1c_evaluation_2_constructor_pilot import OUT as PILOT
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import execute_candidate, validate_candidate, verified_local_image

OUT = PILOT.parent / "e1c2-dev-constructor-rule-v1"
_REQUEST = re.compile(
    r"(?i)\bexpose\s+`(?P<parameter>[A-Za-z_]\w*)`\s+in\s+"
    r"`(?P<class_name>[A-Za-z_]\w*)\.__init__\(\)`,\s+default\s+`(?P<default>True|False)`"
)


def source_from_public_issue(issue: str, quote: str) -> str:
    match = _REQUEST.fullmatch(quote)
    if not match or quote not in issue:
        raise ValueError("public issue does not contain an exact Boolean constructor request")
    class_name = match["class_name"]
    fqns = set(re.findall(rf"`([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+\.{class_name})`", issue))
    if len(fqns) != 1:
        raise ValueError(f"expected one public import path for {class_name}, found {len(fqns)}")
    module = next(iter(fqns)).removesuffix("." + class_name)
    parameter = match["parameter"]
    default = match["default"]
    enabled = "False" if default == "True" else "True"
    return (
        f"from {module} import {class_name}\n"
        f"baseline = {class_name}()\n"
        f"assert baseline.{parameter} is {default}\n"
        f"changed = {class_name}({parameter}={enabled})\n"
        f"assert changed.{parameter} is {enabled}\n"
    )


def run() -> dict:
    freeze_path = PILOT / "freeze.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze.get("schema") != "e1c2-dev-constructor-pilot-freeze-v1":
        raise ValueError("constructor pilot identity missing")
    instance_id = freeze["instance_id"]
    frozen_path = ISSUE / instance_id / "frozen_input_v3.json"
    if _sha(frozen_path) != freeze["input_sha256"]:
        raise ValueError("frozen public issue input changed")
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    source = source_from_public_issue(frozen["issue"], freeze["issue_quote"])
    candidate = validate_candidate(source, freeze["issue_quote"], frozen, workspace=SOURCE / instance_id)
    destination = OUT / instance_id
    result_path = destination / "result.json"
    if result_path.exists() or (destination / "execution").exists():
        raise FileExistsError("constructor-rule DEV replay already started; no silent retry")
    execution = execute_candidate(candidate, verified_local_image(instance_id), frozen["base_commit"],
                                  destination / "execution", repeat_nonsetup_failure=True)
    result = {
        "schema": "e1c2-dev-constructor-rule-v1", "instance_id": instance_id,
        "freeze_sha256": _sha(freeze_path), "input_sha256": _sha(frozen_path),
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "source_provenance": "deterministic_public_boolean_constructor_rule_not_model_response",
        "issue_quote": freeze["issue_quote"], "execution": execution,
        "provider_calls": 0, "trusted_reproducer": False,
    }
    _save(result_path, result)
    return {"instance_id": instance_id, "reasons": [row["reason"] for row in execution["runs"]],
            "repeatable_nonsetup_failure": execution["repeatable_nonsetup_failure"],
            "provider_calls": 0, "trusted_reproducer": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run",))
    parser.parse_args()
    print(json.dumps(run(), ensure_ascii=False))


if __name__ == "__main__":
    main()
