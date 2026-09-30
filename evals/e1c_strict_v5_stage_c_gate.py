"""Playbook Stage-C frozen DEV30 failure-taxonomy gate."""

from __future__ import annotations

import json
from pathlib import Path

from evals.e1c_admission import ROOT

TAXONOMY = ROOT / "data" / "e1c_strict_v5_failure_taxonomy.json"
PARETO = ROOT / "data" / "e1c_strict_v5_failure_pareto.json"
OUT = ROOT / "data" / "e1c_strict_v5_stage_c_gate.json"


def build(output: Path = OUT) -> dict:
    taxonomy = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    pareto = json.loads(PARETO.read_text(encoding="utf-8"))
    rows = taxonomy.get("rows", [])
    ids = [row.get("instance_id") for row in rows]
    categories = pareto.get("categories", [])
    checks = {
        "denominator_30": taxonomy.get("denominator") == 30,
        "row_count_30": len(rows) == 30,
        "unique_identity_count_30": len(set(ids)) == 30 and None not in ids,
        "every_row_has_primary_failure": all(bool(row.get("primary_failure")) for row in rows),
        "runtime_answer_hints_not_exported": taxonomy.get("runtime_answer_hints_exported")
        is False,
        "zero_provider_calls": taxonomy.get("provider_calls") == 0
        and pareto.get("provider_calls") == 0,
        "pareto_denominator_30": pareto.get("denominator") == 30,
        "pareto_aggregate_only": pareto.get("runtime_input")
        == "aggregate_categories_only",
        "pareto_counts_cover_30": sum(
            int(row.get("count", 0)) for row in categories
        )
        == 30,
    }
    ready = all(checks.values())
    result = {
        "schema": "e1c-strict-v5-stage-c-gate-v1",
        "stage_c_ready": ready,
        "reason": "stage_c_taxonomy_ready" if ready else "stage_c_taxonomy_incomplete",
        "checks": checks,
        "denominator": taxonomy.get("denominator"),
        "provider_calls": 0,
        "live_model_run": False,
        "live_allowed": False,
        "c5_allowed": False,
        "fresh30_allowed": False,
        "engineering_gate_only": True,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
