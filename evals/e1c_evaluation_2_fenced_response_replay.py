"""Zero-provider replay of exact outer-JSON-fenced responses from the saved DEV batch."""

from __future__ import annotations

import argparse
import json
import re

from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_dev_batch_replay import OUT as FIRST_REPLAY
from evals.e1c_evaluation_2_dev_batch_v2 import OUT as PILOT
from evals.e1c_evaluation_2_dev_batch_v2 import _quote
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import execute_candidate, validate_candidate, verified_local_image

OUT = ROOT / ".codex/e1c/evaluation_2/e1c2-dev-batch-v2-fence-replay-v1"
_FENCE = re.compile(r"\s*```(?:json)?\s*\n(?P<body>\{.*\})\s*\n```\s*", re.S)


def parse_fenced_source(raw: str) -> str:
    match = _FENCE.fullmatch(raw)
    if match is None:
        raise ValueError("response is not one JSON code fence")
    value = json.loads(match["body"])
    if not isinstance(value, dict) or set(value) != {"source"}:
        raise ValueError("fenced response has unexpected fields")
    return value["source"]


def run() -> dict:
    freeze = json.loads((PILOT / "freeze.json").read_text(encoding="utf-8"))
    results = []
    for row in freeze["tasks"]:
        instance_id = row["instance_id"]
        first = json.loads((FIRST_REPLAY / instance_id / "result.json").read_text(encoding="utf-8"))
        response_path = PILOT / instance_id / "response.json"
        response = json.loads(response_path.read_text(encoding="utf-8"))
        if first.get("status") != "candidate_rejected" or _sha(response_path) != first["response_sha256"]:
            continue
        try:
            source = parse_fenced_source(response["raw"])
        except (ValueError, json.JSONDecodeError):
            continue
        frozen_path = ISSUE / instance_id / "frozen_input_v3.json"
        if _sha(frozen_path) != row["input_sha256"]:
            raise ValueError("public issue input changed")
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
        destination = OUT / instance_id
        result_path = destination / "result.json"
        if result_path.exists() or (destination / "execution").exists():
            raise FileExistsError("fenced response already replayed; no silent retry")
        candidate = validate_candidate(source, _quote(frozen), frozen, workspace=SOURCE / instance_id)
        execution = execute_candidate(
            candidate, verified_local_image(instance_id), frozen["base_commit"],
            destination / "execution", repeat_nonsetup_failure=True,
        )
        result = {
            "schema": "e1c2-dev-batch-v2-fence-replay-v1", "instance_id": instance_id,
            "response_sha256": _sha(response_path), "input_sha256": _sha(frozen_path),
            "probe_sha256": candidate["probe_sha256"], "execution": execution,
            "source_provenance": "saved_model_response_outer_json_fence_removed",
            "provider_calls": 0, "trusted_reproducer": False,
        }
        _save(result_path, result)
        results.append({
            "instance_id": instance_id,
            "repeatable_failure_candidate": execution["repeatable_failure_candidate"],
            "repeatable_nonsetup_failure": execution["repeatable_nonsetup_failure"],
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
