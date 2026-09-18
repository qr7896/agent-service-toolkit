import json
from collections import Counter
from pathlib import Path

from evals.protocol_paths import TASKS
from evals.swe_tasks import load_tasks

OUT = Path("evals/results/e1_complexity_audit.json")


def classify(spec):
    source_files = set(spec.setup_files)
    gold_files = set(spec.gold_sources)
    tests = list(spec.FAIL_TO_PASS) + list(spec.PASS_TO_PASS)
    text = "\n".join(
        [spec.problem_statement, *spec.setup_files.values(), *spec.gold_sources.values()]
    )
    return {
        "instance_id": spec.instance_id,
        "source_files": len(source_files),
        "gold_files": len(gold_files),
        "test_nodes": len(tests),
        "pass_to_pass": len(spec.PASS_TO_PASS),
        "multi_file_gold": len(gold_files) >= 2,
        "async_signal": "async " in text or "await " in text,
        "state_signal": any(
            x in text.lower() for x in ("state", "resume", "persist", "checkpoint", "survival")
        ),
        "config_signal": any(
            Path(f).suffix in {".yml", ".yaml", ".toml", ".json"} for f in gold_files
        ),
        "regression_trap": len(spec.PASS_TO_PASS) >= 2,
    }


def main():
    rows = [classify(t) for t in load_tasks(TASKS)]
    report = {
        "tasks": len(rows),
        "multi_file_gold": sum(r["multi_file_gold"] for r in rows),
        "async_signal": sum(r["async_signal"] for r in rows),
        "state_signal": sum(r["state_signal"] for r in rows),
        "config_signal": sum(r["config_signal"] for r in rows),
        "regression_trap": sum(r["regression_trap"] for r in rows),
        "gold_file_count_distribution": dict(
            sorted(Counter(r["gold_files"] for r in rows).items())
        ),
        "test_node_count_distribution": dict(
            sorted(Counter(r["test_nodes"] for r in rows).items())
        ),
        "rows": rows,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps({k: v for k, v in report.items() if k != "rows"}, ensure_ascii=False, indent=2)
    )


if __name__ == "__main__":
    main()
