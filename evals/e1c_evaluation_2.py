"""Zero-model feedback audit for the frozen E1-C evaluation_2 DEV12 cohort.

This does not generate probes, execute Docker, or promote a failure to trusted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from evals.e1c_reproducer_dev_feedback import classify_probe_outcome
from evals.e1c_strict_successor_expected_failure import FailureContract

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ROOT / "data/e1c_reproducer_dev12_identity.json"
LEDGER_SCHEMA = "e1c-evaluation-2-probe-ledger-v1"


def evaluate(identity_bytes: bytes, ledger: dict) -> dict:
    identity = json.loads(identity_bytes)
    if identity.get("role") != "development_only_never_independent_canary_or_fresh30":
        raise ValueError("identity is not frozen DEV12")
    ids = {row["instance_id"] for row in identity["tasks"]}
    if len(ids) != 12 or ledger.get("schema") != LEDGER_SCHEMA or ledger.get("cohort") != "dev12":
        raise ValueError("invalid DEV12 ledger or identity")
    identity_sha = hashlib.sha256(identity_bytes).hexdigest()
    if ledger.get("identity_sha256") != identity_sha:
        raise ValueError("ledger does not match the frozen DEV12 identity")
    rows = ledger.get("rows")
    if not isinstance(rows, list):
        raise ValueError("ledger rows must be a list")
    counts: Counter[str] = Counter()
    seen: set[tuple[str, str]] = set()
    attempted: set[str] = set()
    summaries = []
    for row in rows:
        instance_id, probe_sha = row["instance_id"], row["probe_sha256"]
        if instance_id not in ids or not isinstance(probe_sha, str) or len(probe_sha) != 64:
            raise ValueError("unknown task or invalid probe identity")
        if (instance_id, probe_sha) in seen:
            raise ValueError("duplicate probe identity")
        if row.get("trusted_reproducer") or any(key in row for key in ("test_patch", "gold_patch", "grader_output")):
            raise ValueError("untrusted promotion or grader-only material in probe ledger")
        seen.add((instance_id, probe_sha))
        attempted.add(instance_id)
        public_exception = row.get("public_exception")
        if public_exception is not None:
            if not isinstance(public_exception, dict) or not all(
                isinstance(public_exception.get(key), str) and public_exception[key]
                for key in ("exception_type", "message")
            ):
                raise ValueError("invalid public exception contract")
            public_exception = FailureContract(public_exception["exception_type"], public_exception["message"])
        outcome = classify_probe_outcome(
            returncode=row["returncode"],
            timed_out=row["timed_out"],
            stdout=row["stdout"],
            stderr=row["stderr"],
            public_exception=public_exception,
        )
        counts[outcome["reason"]] += 1
        summaries.append({
            "instance_id": instance_id,
            "probe_sha256": probe_sha,
            "reason": outcome["reason"],
            "candidate_prepatch_failure": outcome["candidate_prepatch_failure"],
            "trusted_reproducer": False,
        })
    return {
        "schema": "e1c-evaluation-2-feedback-audit-v1",
        "cohort": "dev12",
        "identity_sha256": identity_sha,
        "attempted_tasks": len(attempted),
        "total_tasks": 12,
        "probe_count": len(rows),
        "candidate_count": sum(row["candidate_prepatch_failure"] for row in summaries),
        "trusted_reproducer_count": 0,
        "reason_counts": dict(sorted(counts.items())),
        "development_gate_passed": False,
        "next_gate": "issue_alignment_repeatability_exact_base_and_independent_review_required",
        "rows": summaries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path, help="DEV12 probe ledger JSON; no Docker/provider calls")
    args = parser.parse_args()
    print(json.dumps(evaluate(IDENTITY.read_bytes(), json.loads(args.ledger.read_text(encoding="utf-8"))), indent=2))


if __name__ == "__main__":
    main()
