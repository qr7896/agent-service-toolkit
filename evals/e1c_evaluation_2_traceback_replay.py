"""Zero-provider DEV replay of a sealed response with a public exception quote."""

from __future__ import annotations

import argparse
import hashlib
import json
import re

from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import execute_candidate, validate_candidate, verified_local_image
from evals.e1c_evaluation_2_traceback_pilot import OUT as PILOT

OUT = PILOT.parent / "e1c2-dev-traceback-replay-v1"


def public_exception_quote(issue: str) -> str:
    """Find an exact, public exception line; never repair a model quotation by paraphrase."""
    matches = re.findall(r"(?m)^\s*([A-Za-z]+Error:[^\n]+)", issue)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one public exception line, found {len(matches)}")
    return matches[0]


def run() -> dict:
    freeze_path = PILOT / "freeze.json"
    response_path = PILOT / "response.json"
    ledger_path = PILOT / "provider_calls.jsonl"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    response = json.loads(response_path.read_text(encoding="utf-8"))
    events = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
    if (
        freeze.get("schema") != "e1c2-dev-traceback-pilot-freeze-v1"
        or response.get("prompt_sha256") != freeze.get("prompt_sha256")
        or len([event for event in events if event.get("status") == "completed"]) != 1
        or any(event.get("status") in {"ambiguous", "failed"} for event in events)
    ):
        raise ValueError("sealed one-call DEV response identity is not clean")
    instance_id = freeze["instance_id"]
    frozen_path = ISSUE / instance_id / "frozen_input_v3.json"
    if _sha(frozen_path) != freeze["input_sha256"]:
        raise ValueError("frozen public issue input changed")
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    value = json.loads(response["raw"])
    if not isinstance(value, dict) or set(value) != {"source", "issue_quote"}:
        raise ValueError("sealed response did not contain a probe source")
    quote = public_exception_quote(frozen["issue"])
    candidate = validate_candidate(value["source"], quote, frozen, workspace=SOURCE / instance_id)
    result_path = OUT / instance_id / "result.json"
    if result_path.exists() or (result_path.parent / "execution").exists():
        raise FileExistsError("zero-provider replay already started; no silent retry")
    execution = execute_candidate(
        candidate, verified_local_image(instance_id), frozen["base_commit"],
        result_path.parent / "execution", repeat_nonsetup_failure=True,
    )
    result = {
        "schema": "e1c2-dev-traceback-replay-v1", "instance_id": instance_id,
        "freeze_sha256": _sha(freeze_path), "response_sha256": _sha(response_path),
        "input_sha256": _sha(frozen_path), "probe_sha256": hashlib.sha256(value["source"].encode()).hexdigest(),
        "original_issue_quote_rejected": True, "replacement_quote_source": "exact_public_exception_line",
        "replacement_quote": quote, "execution": execution,
        "provider_calls": 0, "trusted_reproducer": False,
    }
    _save(result_path, result)
    return {"instance_id": instance_id, "reasons": [row["reason"] for row in execution["runs"]],
            "repeatable_failure_candidate": execution["repeatable_failure_candidate"],
            "repeatable_nonsetup_failure": execution["repeatable_nonsetup_failure"],
            "provider_calls": 0, "trusted_reproducer": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run",))
    parser.parse_args()
    print(json.dumps(run(), ensure_ascii=False))


if __name__ == "__main__":
    main()
