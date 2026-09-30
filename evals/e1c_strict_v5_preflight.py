"""Zero-provider strict-v5 admission preflight."""

from __future__ import annotations

import argparse
import json

from evals.e1c_strict_v5_gate import c5_gate, canary_gate, fresh30_gate
from evals.e1c_strict_v5_selector import reserve_status


def preflight() -> dict:
    reserve = reserve_status()
    return {
        "schema": "e1c-strict-v5-static-preflight-v1",
        "ready": reserve["ready"],
        "reason": "ready_for_statement_materialization" if reserve["ready"] else reserve["reason"],
        "reserve": reserve,
        "provider_calls": 0,
        "new_task_tree_touched": False,
        "legacy_v4_result_authoritative": False,
        "canary_gate": canary_gate(),
        "c5_gate": c5_gate(),
        "fresh30_gate": fresh30_gate(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight",))
    parser.parse_args()
    result = preflight()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
