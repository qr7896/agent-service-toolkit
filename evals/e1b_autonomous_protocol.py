import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from evals.protocol_paths import E1_B_EVAL_SPLIT, E1_B_TASKS
from evals.swe_tasks import load_tasks

OUT = Path("evals/results/e1b_autonomous_config.json")


@dataclass(frozen=True)
class AutonomousConfig:
    protocol: str = "e1b-autonomous-editor-v0"
    model_mode: str = "not_configured"
    max_iterations: int = 4
    max_files_written: int = 3
    allow_test_file_writes: bool = False
    gold_sources_visible: bool = False
    gold_labels_visible: bool = False
    grader_visible_during_edit: bool = False
    sandbox_required: bool = True
    dev_only_until_freeze: bool = True


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_task(task):
    return {
        "instance_id": task.instance_id,
        "problem_statement": task.problem_statement,
        "setup_files": sorted(task.setup_files),
        "test_files": sorted(task.test_files),
        "repo": task.repo,
        "base_commit": task.base_commit,
        "source_commit": task.source_commit,
    }


def main():
    split = json.loads(E1_B_EVAL_SPLIT.read_text(encoding="utf-8"))
    tasks = {t.instance_id: t for t in load_tasks(E1_B_TASKS)}
    dev = [public_task(tasks[i]) for i in split["dev_ids"]]
    report = {
        "config": asdict(AutonomousConfig()),
        "status": "dev_harness_contract_ready_model_not_configured",
        "claim_boundary": "No autonomous repair result is produced by this protocol file.",
        "dev_task_count": len(dev),
        "sealed_test_task_count": len(split["test_ids"]),
        "dev_tasks_public_view": dev,
        "sealed_test_ids": split["test_ids"],
        "inputs": {
            str(E1_B_TASKS): sha(E1_B_TASKS),
            str(E1_B_EVAL_SPLIT): sha(E1_B_EVAL_SPLIT),
        },
        "failure_decomposition": {
            "retrieval_gap": "retrieved evidence is insufficient for constrained Oracle repair",
            "editor_reasoning_gap": "Oracle resolves under matched evidence but Autonomous Editor does not",
            "regression_gap": "FAIL_TO_PASS is repaired but PASS_TO_PASS regresses",
        },
        "freeze_gate": [
            "Choose model/provider on DEV only.",
            "Freeze prompt, tools, iteration budget, write policy, and model identifier before TEST.",
            "Hash the final autonomous configuration before opening TEST outcomes.",
            "Never expose gold_sources, gold_files, gold_symbols, gold_callers, gold_tests, or gold_context to the editor.",
        ],
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {"status": report["status"], "dev": len(dev), "sealed_test": len(split["test_ids"])},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
