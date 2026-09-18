import json
import tempfile
from collections import Counter
from pathlib import Path

from evals.protocol_paths import TASKS
from evals.swe_tasks import grade, load_tasks, prepare

E1B = Path("evals/tasks/e1b_candidates.jsonl")
OUT = Path("evals/results/e1b_pool_audit.json")


def stats(spec):
    text = "\n".join(
        [spec.problem_statement, *spec.setup_files.values(), *spec.gold_sources.values()]
    )
    return {
        "instance_id": spec.instance_id,
        "cluster": spec.cluster,
        "source_commit": spec.source_commit,
        "gold_files": len(spec.gold_sources),
        "test_nodes": len(spec.FAIL_TO_PASS) + len(spec.PASS_TO_PASS),
        "pass_to_pass": len(spec.PASS_TO_PASS),
        "async_signal": "async " in text or "await " in text,
        "state_signal": any(
            x in text.lower() for x in ("state", "resume", "persist", "checkpoint", "approval")
        ),
        "config_signal": any(
            Path(f).suffix in {".json", ".yaml", ".yml", ".toml"} for f in spec.gold_sources
        ),
        "hard_negative_signal": len(set(spec.setup_files) - set(spec.gold_sources)) > 0,
    }


def main():
    old = load_tasks(TASKS)
    new = load_tasks(E1B)
    all_tasks = old + new
    ids = [t.instance_id for t in all_tasks]
    integrity = []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        for t in new:
            base = grade(t, prepare(t, root / (t.instance_id + "-base")))
            gold = grade(t, prepare(t, root / (t.instance_id + "-gold"), True))
            integrity.append(
                {
                    "instance_id": t.instance_id,
                    "base_unresolved": not base["resolved"],
                    "gold_resolved": gold["resolved"],
                }
            )
    rows = [stats(t) for t in all_tasks]
    report = {
        "pool_tasks": len(all_tasks),
        "existing_tasks": len(old),
        "e1b_tasks": len(new),
        "unique_instance_ids": len(ids) == len(set(ids)),
        "existing_unique_source_commits": len({t.source_commit for t in old}),
        "e1b_unique_source_commits": len({t.source_commit for t in new}) == len(new),
        "cross_pool_source_commit_overlap": sorted(
            {t.source_commit for t in old} & {t.source_commit for t in new}
        ),
        "e1b_integrity_valid": all(x["base_unresolved"] and x["gold_resolved"] for x in integrity),
        "e1b_base_unresolved": sum(x["base_unresolved"] for x in integrity),
        "e1b_gold_resolved": sum(x["gold_resolved"] for x in integrity),
        "gold_file_distribution": dict(sorted(Counter(r["gold_files"] for r in rows).items())),
        "test_node_distribution": dict(sorted(Counter(r["test_nodes"] for r in rows).items())),
        "multi_file_gold": sum(r["gold_files"] >= 2 for r in rows),
        "async_signal": sum(r["async_signal"] for r in rows),
        "state_signal": sum(r["state_signal"] for r in rows),
        "config_signal": sum(r["config_signal"] for r in rows),
        "hard_negative_signal": sum(r["hard_negative_signal"] for r in rows),
        "multi_p2p": sum(r["pass_to_pass"] >= 2 for r in rows),
        "e1b_integrity": integrity,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {k: v for k, v in report.items() if k != "e1b_integrity"}, ensure_ascii=False, indent=2
        )
    )
    assert (
        report["pool_tasks"] == 30
        and report["unique_instance_ids"]
        and report["e1b_unique_source_commits"]
        and not report["cross_pool_source_commit_overlap"]
        and report["e1b_integrity_valid"]
    )


if __name__ == "__main__":
    main()
