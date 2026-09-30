import json
from pathlib import Path

from evals.e1b_autonomous_harness import dev_tasks, sanitize_editor_payload
from evals.e1b_contract_extractor_v6 import extract_contract
from evals.e1b_state_transition_v8 import build_transition_contract

RESULT = Path("evals/results/e1b_autonomous_dev_run_v8.json")
LEDGER = Path(".codex/e1b/r10-v8/provider_calls.jsonl")
SCHEMA = "e1b-state-transition-v1"


def preflight():
    rows = []
    for task in dev_tasks():
        payload = sanitize_editor_payload(task, {"problem_statement": task.problem_statement})
        contract = build_transition_contract(extract_contract(payload["problem_statement"]))
        rows.append(
            {
                "instance_id": task.instance_id,
                "schema_version": contract["schema_version"],
                "target_obligations": len(contract["target_obligations"]),
                "preservation_obligations": len(contract["preservation_obligations"]),
            }
        )
    schema_valid = all(row["schema_version"] == SCHEMA for row in rows)
    return {
        "protocol": "e1b-r10-v8-offline-preflight-v1",
        "provider_calls": 0,
        "schema_version": SCHEMA,
        "tasks": len(rows),
        "schema_valid": schema_valid,
        "result_exists": RESULT.exists(),
        "ledger_exists": LEDGER.exists(),
        "ready_for_runner_freeze": (
            len(rows) == 4 and schema_valid and not RESULT.exists() and not LEDGER.exists()
        ),
        "live_authorized": False,
        "rows": rows,
        "claim_boundary": "offline schema/preflight only; no model call and no patch efficacy claim",
    }


def main():
    print(json.dumps(preflight(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
