"""Reproducer-v4 paired-canary runner built on the frozen v3 execution shell."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from evals import e1c_blind_repro_v3_runner as base
from evals.e1c_admission import ROOT
from evals.e1c_blind_repro_v4_selector import (
    CANARY_COUNT,
    canary_rows,
    frozen_selector_identity,
    reserve_status,
)
from evals.e1c_blind_reproducer_v4 import (
    freeze_probe_plan_v4,
    repair_probe_context_v4,
    run_prepatch_probes_v4,
)

RUN_ID = "e1c-blind-reproducer-c4r-v4-v1"
PREP_ID = "e1c-blind-reproducer-c4r-v4-prep-v1"
OUT = ROOT / ".codex" / "e1c"
RUN_DIR = OUT / RUN_ID
PREP_DIR = OUT / PREP_ID
MIN_REPRODUCER_COUNT = 2


def _configure_base() -> None:
    base.RUN_ID = RUN_ID
    base.PREP_ID = PREP_ID
    base.RUN_DIR = RUN_DIR
    base.PREP_DIR = PREP_DIR
    base.LEDGER = RUN_DIR / "provider_calls.jsonl"
    base.CANARY_COUNT = CANARY_COUNT
    base.MIN_REPRODUCER_COUNT = MIN_REPRODUCER_COUNT
    base.canary_rows = canary_rows
    base.frozen_selector_identity = frozen_selector_identity
    base.freeze_probe_plan = freeze_probe_plan_v4
    base.run_prepatch_probes = run_prepatch_probes_v4
    base.repair_probe_context = repair_probe_context_v4


def static_preflight() -> dict:
    status = reserve_status()
    if not status["ready"]:
        return {
            "schema": "e1c-blind-reproducer-v4-static-preflight-v1",
            "ready": False,
            "reason": status["reason"],
            "reserve": status,
            "provider_calls": 0,
            "new_task_tree_touched": False,
        }
    _configure_base()
    result = base.static_preflight()
    return {
        **result,
        "schema": "e1c-blind-reproducer-v4-static-preflight-v1",
        "mechanism": "issue-derived-behavioral-witness-v4",
        "new_task_tree_touched": False,
    }


def prepare() -> dict:
    _configure_base()
    result = base.prepare()
    result = {
        **result,
        "schema": "e1c-blind-reproducer-v4-prepared-v1",
        "mechanism": "issue-derived-behavioral-witness-v4",
        "development_reference_coverage": "3/3_contaminated_dev_only",
    }
    base._save(PREP_DIR / "prepared.json", result)
    return result


def live_preflight() -> dict:
    _configure_base()
    result = base.live_preflight()
    return {
        **result,
        "schema": "e1c-blind-reproducer-v4-live-preflight-v1",
        "required_reproduced_count": MIN_REPRODUCER_COUNT,
        "new_task_tree_touched": False,
    }


def _summary(rows: list[dict]) -> dict:
    baseline = {r["instance_id"] for r in rows if r["arm"] == "baseline" and r["resolved"]}
    treatment = {r["instance_id"] for r in rows if r["arm"] == "treatment" and r["resolved"]}
    invalid_statuses = {"invalid_action", "invalid_final_action"}
    anomalies = sorted(
        f"{r['instance_id']}:{r['arm']}:{r['status']}"
        for r in rows
        if r.get("status") in invalid_statuses
        or (r.get("status") == "graded" and r.get("grade_valid_log") is not True)
    )
    provider_tokens = sum(
        usage.get("total_tokens", 0)
        for row in rows
        for usage in row.get("usages", ([row["first_usage"]] if "first_usage" in row else []))
    )
    treatment_only = sorted(treatment - baseline)
    baseline_only = sorted(baseline - treatment)
    return {
        "schema": "e1c-blind-reproducer-v4-c4r-result-v1",
        "rows": rows,
        "baseline_resolved": len(baseline),
        "treatment_resolved": len(treatment),
        "treatment_only_resolved": treatment_only,
        "baseline_only_resolved": baseline_only,
        "net_new_resolved": len(treatment_only),
        "provider_tokens": provider_tokens,
        "identity_anomalies": anomalies,
        "expand_c5": bool(treatment_only) and not baseline_only and not anomalies,
    }


async def run_canary() -> dict:
    _configure_base()
    gate = live_preflight()
    if not gate["ready"]:
        raise RuntimeError(f"reproducer-v4 live preflight not ready: {gate}")
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    identity = {
        **gate,
        "protocol": "e1c-blind-reproducer-c4r-v4-v1",
        "mechanism": "issue-derived-behavioral-witness-v4",
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "reproducer_sha256": hashlib.sha256(
            Path(run_prepatch_probes_v4.__code__.co_filename).read_bytes()
        ).hexdigest(),
        "stop_rule": (
            "C5 only if >=1 treatment-only official resolved, 0 baseline-only official "
            "resolved, and no identity/safety/budget/infrastructure anomaly"
        ),
    }
    base._save(RUN_DIR / "identity.json", identity)
    outcomes: list[dict] = []
    for row in canary_rows():
        for arm in ("baseline", "treatment"):
            try:
                outcome = await base._arm(row, arm)
            except Exception as exc:
                base._save(
                    RUN_DIR / "state.json",
                    {
                        "schema": "e1c-blind-reproducer-v4-c4r-state-v1",
                        "rows": outcomes,
                        "status": "interrupted_no_auto_retry",
                        "interrupted": f"{row['instance_id']}:{arm}",
                        "error": f"{type(exc).__name__}: {exc}",
                    },
                )
                raise
            outcomes.append(outcome)
            base._save(
                RUN_DIR / "state.json",
                {"schema": "e1c-blind-reproducer-v4-c4r-state-v1", "rows": outcomes},
            )
    summary = _summary(outcomes)
    base._save(RUN_DIR / "result.json", summary)
    return summary


def c5_gate() -> dict:
    result_path = RUN_DIR / "result.json"
    if not result_path.is_file():
        return {
            "schema": "e1c-blind-reproducer-v4-c5-gate-v1",
            "ready": False,
            "reason": "C4R_V4_not_run",
            "new_task_tree_touched": False,
        }
    result = json.loads(result_path.read_text(encoding="utf-8"))
    ready = result.get("expand_c5") is True
    return {
        "schema": "e1c-blind-reproducer-v4-c5-gate-v1",
        "ready": ready,
        "reason": "C4R_V4_passed" if ready else "C4R_V4_stop_rule_not_met",
        "treatment_only_resolved": result.get("treatment_only_resolved", []),
        "baseline_only_resolved": result.get("baseline_only_resolved", []),
        "identity_anomalies": result.get("identity_anomalies", []),
        "c4r_result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "new_task_tree_touched": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("preflight", "prepare", "live-preflight", "run-canary", "c5-gate"),
    )
    args = parser.parse_args()
    if args.command == "preflight":
        result = static_preflight()
    elif args.command == "prepare":
        result = prepare()
    elif args.command == "live-preflight":
        result = live_preflight()
    elif args.command == "run-canary":
        result = asyncio.run(run_canary())
    else:
        result = c5_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.command in {"preflight", "live-preflight"} and not result["ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
