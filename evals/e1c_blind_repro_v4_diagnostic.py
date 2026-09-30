"""Zero-provider v4 diagnostic on the now-contaminated final three DEV rows."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor

from evals.e1c_admission import ROOT, TASKS
from evals.e1c_blind_reproducer_v2 import build_runtime_view
from evals.e1c_blind_reproducer_v4 import run_prepatch_probes_v4
from evals.e1c_live_runner import _manifest, _source

OUT = ROOT / ".codex" / "e1c" / "e1c-blind-reproducer-v4-dev-diagnostic-v1"
IDS = (
    "django__django-15957",
    "django__django-12754",
    "django__django-15280",
)


def _rows() -> list[dict]:
    by_id = {row["instance_id"]: row for row in _manifest()["tasks"]}
    return [by_id[instance_id] for instance_id in IDS]


def _one(row: dict) -> dict:
    instance_id = row["instance_id"]
    statement = (TASKS / instance_id / "problem_statement.md").read_text(encoding="utf-8")
    source = _source(row)
    view = build_runtime_view(instance_id, statement, source)
    prepatch = run_prepatch_probes_v4(row, view, OUT / "audit" / instance_id)
    return {
        "instance_id": instance_id,
        "reproducer_status": prepatch["reproducer_status"],
        "no_reproducer_reason": prepatch.get("no_reproducer_reason"),
        "selected_reproducer_role": prepatch.get("selected_reproducer_role"),
        "selected_origin": next(
            (
                item.get("origin")
                for item in prepatch["executed_probes"]
                if item["role"] == prepatch.get("selected_reproducer_role")
            ),
            None,
        ),
        "probe_count": len(prepatch["executed_probes"]),
        "freeze_sha256": prepatch["freeze_sha256"],
    }


def run() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as executor:
        rows = list(executor.map(_one, _rows()))
    reproduced = sum(row["reproducer_status"] == "reproduced_failure" for row in rows)
    result = {
        "schema": "e1c-blind-reproducer-v4-dev-diagnostic-v1",
        "provider_calls": 0,
        "development_contaminated": True,
        "independent_canary_claim": False,
        "task_count": len(rows),
        "reproduced_count": reproduced,
        "coverage": f"{reproduced}/{len(rows)}",
        "rows": rows,
    }
    (OUT / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run",))
    parser.parse_args()
    print(json.dumps(run(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
