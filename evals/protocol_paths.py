from pathlib import Path

TASKS = Path("evals/tasks/research_v0.jsonl")
V1_CLUSTER_SPLIT = {
    "validation": "train",
    "observability": "train",
    "policy-gate": "train",
    "input-normalization": "train",
    "evidence-decision": "train",
    "memory-quality": "dev",
    "workflow-composition": "dev",
    "sandbox-output": "test",
    "durable-approval": "test",
}
RESULTS = Path("evals/results")
V1_MANIFEST = RESULTS / "v1_frozen_manifest.json"
V1_REPLAY = RESULTS / "v1_frozen_replay.json"
V0_MATCHED = RESULTS / "v1_matched_v0_utility.json"
V1_GO_NO_GO = RESULTS / "v1_go_no_go.json"
E1_MANIFEST = Path("evals/e1_manifest.json")
E1_SMOKE = RESULTS / "e1_smoke_oracle_editor.json"
E1_DATASET_AUDIT = RESULTS / "e1_dataset_audit.json"
E1_TASK_INTEGRITY = RESULTS / "e1_task_integrity.json"
E1_COMPLEXITY_AUDIT = RESULTS / "e1_complexity_audit.json"
E1_B_TASKS = Path("evals/tasks/e1b_candidates.jsonl")
E1_B_POOL_AUDIT = RESULTS / "e1b_pool_audit.json"
E1_B_FREEZE = RESULTS / "e1b_freeze_manifest.json"
E1_B_EVAL_SPLIT = RESULTS / "e1b_evaluation_split.json"

__all__ = [
    "TASKS",
    "V1_CLUSTER_SPLIT",
    "RESULTS",
    "V1_MANIFEST",
    "V1_REPLAY",
    "V0_MATCHED",
    "V1_GO_NO_GO",
    "E1_MANIFEST",
    "E1_SMOKE",
    "E1_DATASET_AUDIT",
    "E1_TASK_INTEGRITY",
    "E1_COMPLEXITY_AUDIT",
    "E1_B_TASKS",
    "E1_B_POOL_AUDIT",
    "E1_B_FREEZE",
    "E1_B_EVAL_SPLIT",
]
