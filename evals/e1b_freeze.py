import hashlib
import json
from datetime import date
from pathlib import Path

from evals.protocol_paths import TASKS
from evals.swe_tasks import load_tasks

E1B = Path("evals/tasks/e1b_candidates.jsonl")
AUDIT = Path("evals/results/e1b_pool_audit.json")
OUT = Path("evals/results/e1b_freeze_manifest.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    old = load_tasks(TASKS)
    new = load_tasks(E1B)
    assert audit["pool_tasks"] == 30
    assert audit["e1b_integrity_valid"]
    assert audit["e1b_unique_source_commits"]
    assert not audit["cross_pool_source_commit_overlap"]
    manifest = {
        "protocol": "e1b-freeze-candidate-v1",
        "created": str(date.today()),
        "claim_boundary": "Executable 30-task pool; not an untouched 30-task held-out test and not autonomous Coding Agent success.",
        "pool": {"tasks": 30, "existing": 20, "e1b": 10},
        "files": {
            str(TASKS): sha(TASKS),
            str(E1B): sha(E1B),
            str(AUDIT): sha(AUDIT),
        },
        "e1b_instance_ids": [t.instance_id for t in new],
        "e1b_source_commits": [t.source_commit for t in new],
        "existing_source_commits": sorted({t.source_commit for t in old}),
        "cross_pool_source_commit_overlap": audit["cross_pool_source_commit_overlap"],
        "integrity": {
            "e1b_base_unresolved": audit["e1b_base_unresolved"],
            "e1b_gold_resolved": audit["e1b_gold_resolved"],
        },
        "complexity": {
            k: audit[k]
            for k in (
                "gold_file_distribution",
                "test_node_distribution",
                "multi_file_gold",
                "async_signal",
                "state_signal",
                "config_signal",
                "hard_negative_signal",
                "multi_p2p",
            )
        },
        "next_protocol": "Create a new explicit E1-B evaluation split/freeze before autonomous-editor comparison; do not relabel the opened V1 frozen test.",
    }
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
