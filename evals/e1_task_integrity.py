import json
import tempfile
from pathlib import Path

from evals.protocol_paths import TASKS, V1_CLUSTER_SPLIT
from evals.swe_tasks import grade, load_tasks, prepare

OUT = Path("evals/results/e1_task_integrity.json")


def main():
    rows = []
    with tempfile.TemporaryDirectory(prefix="e1-integrity-") as temp:
        root = Path(temp)
        for spec in load_tasks(TASKS):
            base = root / f"{spec.instance_id}-base"
            gold = root / f"{spec.instance_id}-gold"
            prepare(spec, base)
            prepare(spec, gold, with_gold=True)
            base_grade = grade(spec, base)
            gold_grade = grade(spec, gold)
            rows.append(
                {
                    "instance_id": spec.instance_id,
                    "split": V1_CLUSTER_SPLIT[spec.cluster],
                    "cluster": spec.cluster,
                    "base_unresolved": not base_grade["resolved"],
                    "gold_resolved": gold_grade["resolved"],
                    "base_grade": base_grade,
                    "gold_grade": gold_grade,
                }
            )
    invalid = [r["instance_id"] for r in rows if not r["base_unresolved"] or not r["gold_resolved"]]
    report = {
        "tasks": len(rows),
        "base_unresolved": sum(r["base_unresolved"] for r in rows),
        "gold_resolved": sum(r["gold_resolved"] for r in rows),
        "valid_tasks": sum(r["base_unresolved"] and r["gold_resolved"] for r in rows),
        "invalid_tasks": invalid,
        "rows": rows,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps({k: v for k, v in report.items() if k != "rows"}, ensure_ascii=False, indent=2)
    )
    if invalid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
