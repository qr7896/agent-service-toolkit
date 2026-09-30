import json
from pathlib import Path

from evals.e1b_autonomous_harness import dev_tasks
from evals.e1b_contract_extractor_v6 import extract_contract
from evals.e1b_state_transition_v8 import (
    build_transition_contract,
)

RESULT = Path("evals/results/e1b_autonomous_dev_run_v7b.json")
OUT = Path("evals/results/e1b_state_transition_v8_offline_audit.json")


def main():
    report = json.loads(RESULT.read_text(encoding="utf-8"))
    tasks = {task.instance_id: task for task in dev_tasks()}
    rows = []
    for row in report["rows"]:
        task = tasks[row["instance_id"]]
        behavioral = extract_contract(task.problem_statement)
        transition = build_transition_contract(behavioral)
        # v7 stores hashes/files, not patch bodies; this audit intentionally reports
        # contract obligations only and does not reconstruct hidden or grader data.
        rows.append(
            {
                "instance_id": task.instance_id,
                "resolved": row["resolved"],
                "transition_contract": transition,
                "offline_patch_audit_available": False,
                "reason": "v7 result artifact intentionally does not persist patch bodies",
            }
        )
    result = {
        "protocol": "e1b-v8-state-transition-contract-offline-audit-v1",
        "provider_calls": 0,
        "scope": "public DEV problem statements + v7 public result metadata only",
        "rows": rows,
        "claim_boundary": (
            "Contract extraction is auditable offline; patch-level transition checking requires "
            "candidate patch content and is not inferred from hashes, tests, grader, or gold."
        ),
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
