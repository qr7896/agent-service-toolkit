import hashlib
import json
from pathlib import Path

from evals.protocol_paths import E1_B_FREEZE, E1_B_TASKS
from evals.swe_tasks import load_tasks

OUT = Path("evals/results/e1b_evaluation_split.json")

DEV_IDS = {
    "e1b__async-propagation-22",
    "e1b__config-code-budget-25",
    "e1b__cross-module-status-26",
    "e1b__state-version-29",
}
TEST_IDS = {
    "e1b__multifile-policy-21",
    "e1b__resume-approval-23",
    "e1b__symbol-hard-negative-24",
    "e1b__async-cancel-27",
    "e1b__hard-negative-router-28",
    "e1b__multifile-sandbox-cleanup-30",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    tasks = load_tasks(E1_B_TASKS)
    ids = {t.instance_id for t in tasks}
    assert DEV_IDS | TEST_IDS == ids
    assert not DEV_IDS & TEST_IDS
    by_id = {t.instance_id: t for t in tasks}
    dev_commits = {by_id[i].source_commit for i in DEV_IDS}
    test_commits = {by_id[i].source_commit for i in TEST_IDS}
    assert not dev_commits & test_commits
    freeze = json.loads(E1_B_FREEZE.read_text(encoding="utf-8"))
    report = {
        "protocol": "e1b-evaluation-split-v1",
        "status": "frozen_before_autonomous_editor",
        "claim_boundary": "New E1-B candidate tasks only; separate from the previously opened V1 frozen test.",
        "selection_rule": "Deterministic pre-autonomous-editor split chosen to place 4 tasks in development and 6 tasks in evaluation while retaining multi-file, async, state, and hard-negative cases in evaluation.",
        "dev_ids": sorted(DEV_IDS),
        "test_ids": sorted(TEST_IDS),
        "dev_count": len(DEV_IDS),
        "test_count": len(TEST_IDS),
        "dev_source_commits": sorted(dev_commits),
        "test_source_commits": sorted(test_commits),
        "source_commit_overlap": sorted(dev_commits & test_commits),
        "inputs": {
            str(E1_B_TASKS): sha(E1_B_TASKS),
            str(E1_B_FREEZE): sha(E1_B_FREEZE),
        },
        "parent_freeze_protocol": freeze["protocol"],
        "rules": [
            "Do not tune Autonomous Editor prompts, tools, or policy against test outcomes.",
            "Use dev tasks for implementation debugging and prompt/tool selection.",
            "Open the six test outcomes only after the autonomous configuration is frozen.",
            "Gold sources and Gold labels are grader-only and unavailable to Autonomous Editor.",
            "Report Oracle and Autonomous results separately.",
        ],
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
