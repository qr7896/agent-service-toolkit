"""Zero-provider replay of saved DEV batch responses after a generic import-validator fix."""

from __future__ import annotations

import argparse
import json

from evals.e1c_blind_boundary import BlindBoundaryViolation
from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_dev_batch_v2 import OUT as PILOT
from evals.e1c_evaluation_2_dev_batch_v2 import _quote
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import execute_candidate, validate_candidate, verified_local_image

OUT = ROOT / ".codex/e1c/evaluation_2/e1c2-dev-batch-v2-replay-v1"


def run() -> dict:
    freeze = json.loads((PILOT / "freeze.json").read_text(encoding="utf-8"))
    state = json.loads((PILOT / "state.json").read_text(encoding="utf-8"))
    if freeze.get("schema") != "e1c2-dev-batch-v2-freeze" or state.get("status") != "completed":
        raise ValueError("original DEV batch incomplete")
    results = []
    for row in freeze["tasks"]:
        instance_id = row["instance_id"]
        frozen_path = ISSUE / instance_id / "frozen_input_v3.json"
        response_path = PILOT / instance_id / "response.json"
        if _sha(frozen_path) != row["input_sha256"]:
            raise ValueError("public input changed after pilot")
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
        response = json.loads(response_path.read_text(encoding="utf-8"))
        if response["prompt_sha256"] != row["prompt_sha256"]:
            raise ValueError("response prompt does not match freeze")
        destination = OUT / instance_id
        result_path = destination / "result.json"
        if result_path.exists() or (destination / "execution").exists():
            raise FileExistsError("saved response already replayed; no silent retry")
        result = {
            "schema": "e1c2-dev-batch-v2-replay-v1", "instance_id": instance_id,
            "freeze_sha256": _sha(PILOT / "freeze.json"), "response_sha256": _sha(response_path),
            "input_sha256": _sha(frozen_path), "provider_calls": 0,
            "source_provenance": "saved_model_response_from_e1c2-dev-batch-v2",
            "trusted_reproducer": False,
        }
        try:
            payload = json.loads(response["raw"])
            if not isinstance(payload, dict) or set(payload) != {"source"}:
                raise ValueError("response is not one Python source field")
            candidate = validate_candidate(payload["source"], _quote(frozen), frozen, workspace=SOURCE / instance_id)
            result["probe_sha256"] = candidate["probe_sha256"]
            execution = execute_candidate(
                candidate, verified_local_image(instance_id), frozen["base_commit"],
                destination / "execution", repeat_nonsetup_failure=True,
            )
            result["execution"] = execution
            result["status"] = "executed"
        except (BlindBoundaryViolation, ValueError, SyntaxError, TypeError) as exc:
            result.update({"status": "candidate_rejected", "reason": f"{type(exc).__name__}: {exc}"})
        _save(result_path, result)
        results.append({
            "instance_id": instance_id, "status": result["status"],
            "repeatable_failure_candidate": result.get("execution", {}).get("repeatable_failure_candidate", False),
            "repeatable_nonsetup_failure": result.get("execution", {}).get("repeatable_nonsetup_failure", False),
        })
        print(json.dumps(results[-1], ensure_ascii=False), flush=True)
    return {"provider_calls": 0, "rows": results, "trusted_reproducer_count": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run",))
    parser.parse_args()
    print(json.dumps(run(), ensure_ascii=False))


if __name__ == "__main__":
    main()
