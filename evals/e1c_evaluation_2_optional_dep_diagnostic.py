"""Zero-provider DEV diagnostic of a public-issue optional-dependency precondition."""

from __future__ import annotations

import argparse
import hashlib
import json

from evals.e1c_evaluation_2_dev_pilot import TASKS, _save, _sha
from evals.e1c_evaluation_2_feedback_pilot import REPLAY, ROOT_OUT, _prior
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import (
    execute_candidate,
    issue_missing_optional_import,
    validate_candidate,
    verified_local_image,
)

OUT = ROOT_OUT / "e1c2-optional-dep-dev-diagnostic-v2"


def run(instance_id: str) -> dict:
    if instance_id not in TASKS:
        raise ValueError("diagnostic requires a frozen DEV pilot task")
    replay = json.loads(REPLAY.read_text(encoding="utf-8"))
    if replay.get("schema") != "e1c2-dev-probe-replay-v4" or replay.get("provider_calls") != 0:
        raise ValueError("prior zero-call replay changed")
    frozen_path = ISSUE / instance_id / "frozen_input_v3.json"
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    missing_import = issue_missing_optional_import(frozen)
    if not missing_import:
        raise ValueError("public issue and frozen production windows do not identify one absent optional import")
    source, raw, prior_sha = _prior(instance_id, replay)
    candidate = validate_candidate(
        source, json.loads(raw)["issue_quote"], frozen, workspace=SOURCE / instance_id
    )
    artifact_dir = OUT / instance_id
    result_path = artifact_dir / "result.json"
    if result_path.exists() or (artifact_dir / "execution").exists():
        raise FileExistsError("diagnostic already started; no silent retry")
    execution = execute_candidate(
        candidate, verified_local_image(instance_id), frozen["base_commit"], artifact_dir / "execution",
        missing_optional_import=missing_import, repeat_nonsetup_failure=True,
    )
    result = {
        "schema": "e1c2-optional-dep-dev-diagnostic-v2",
        "instance_id": instance_id,
        "issue_input_sha256": _sha(frozen_path),
        "prior_response_sha256": prior_sha,
        "prior_replay_sha256": _sha(REPLAY),
        "probe_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "missing_optional_import": missing_import,
        "execution": execution,
        "provider_calls": 0,
        "trusted_reproducer": False,
    }
    _save(result_path, result)
    return {"instance_id": instance_id, "missing_optional_import": missing_import,
            "reasons": [row["reason"] for row in execution["runs"]],
            "repeatable_failure_candidate": execution["repeatable_failure_candidate"],
            "repeatable_nonsetup_failure": execution["repeatable_nonsetup_failure"],
            "trusted_reproducer": False, "provider_calls": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instance_id")
    args = parser.parse_args()
    print(json.dumps(run(args.instance_id), ensure_ascii=False))


if __name__ == "__main__":
    main()
