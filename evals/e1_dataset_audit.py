import json

from evals.protocol_paths import E1_DATASET_AUDIT, TASKS, V1_CLUSTER_SPLIT
from evals.swe_tasks import load_tasks

OUT = E1_DATASET_AUDIT


def main():
    tasks = load_tasks(TASKS)
    rows = []
    for t in tasks:
        split = V1_CLUSTER_SPLIT[t.cluster]
        rows.append(
            {
                "instance_id": t.instance_id,
                "split": split,
                "cluster": t.cluster,
                "task_type": t.task_type,
                "source_commit": t.source_commit,
                "base_commit": t.base_commit,
                "gold_verified": t.gold_verified,
                "gold_files": len(t.gold_files),
                "gold_sources": len(t.gold_sources),
                "fail_to_pass": len(t.FAIL_TO_PASS),
                "pass_to_pass": len(t.PASS_TO_PASS),
            }
        )
    commits = {
        k: {r["source_commit"] for r in rows if r["split"] == k} for k in ("train", "dev", "test")
    }
    overlaps = {
        f"{a}_{b}": sorted(commits[a] & commits[b])
        for a, b in (("train", "dev"), ("train", "test"), ("dev", "test"))
    }
    report = {
        "tasks": len(rows),
        "split_counts": {k: sum(r["split"] == k for r in rows) for k in ("train", "dev", "test")},
        "clusters": {
            k: sorted({r["cluster"] for r in rows if r["split"] == k})
            for k in ("train", "dev", "test")
        },
        "task_types": sorted({r["task_type"] for r in rows}),
        "gold_verified": sum(r["gold_verified"] for r in rows),
        "tasks_with_f2p": sum(r["fail_to_pass"] > 0 for r in rows),
        "tasks_with_p2p": sum(r["pass_to_pass"] > 0 for r in rows),
        "source_commit_overlap": overlaps,
        "eligible_for_current_frozen_e1": sum(
            r["split"] == "test" and r["gold_verified"] and r["fail_to_pass"] > 0 for r in rows
        ),
        "target_gap_to_30": max(0, 30 - len(rows)),
        "rows": rows,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps({k: v for k, v in report.items() if k != "rows"}, ensure_ascii=False, indent=2)
    )


if __name__ == "__main__":
    main()
