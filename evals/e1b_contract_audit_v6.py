import json

from evals.e1b_autonomous_harness import dev_tasks
from evals.e1b_contract_extractor_v6 import extract_contract


def audit():
    rows = []
    for task in dev_tasks():
        contract = extract_contract(task.problem_statement)
        rows.append(
            {
                "instance_id": task.instance_id,
                "target_change_count": len(contract["target_changes"]),
                "preservation_count": len(contract["preservation_constraints"]),
                "default_transition": contract["default_transition"],
                "has_target": bool(contract["target_changes"]),
            }
        )
    return {
        "protocol": "e1b-v6-public-dev-contract-audit-v1",
        "scope": "DEV public problem statements only",
        "provider_calls": 0,
        "rows": rows,
        "valid": all(row["has_target"] and row["default_transition"] == "identity" for row in rows),
    }


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
