import json

from evals.e1b_experiment_admission_v10_7 import AdmissionConfig, admit
from evals.e1b_freeze_manifest_v10_6 import EXCLUDED_SOURCES


def synthetic_config():
    return AdmissionConfig(
        task_metadata={"task_count": 12, "repo_ids": ["public-repo-a"], "commit_ids": ["abc1234"], "curation_timestamps": ["2026-09-20T00:00:00Z"], "overlap_audit_passed": True, "source_commit_overlap": False, "manifest_sha256": "a" * 64, "base_fail_attested": True, "gold_pass_independently_attested": True},
        data_isolation=EXCLUDED_SOURCES,
        frozen_identifiers={"model_id": "provider/model-v1", "editor_prompt_sha256": "b" * 64, "runtime_sha256": "c" * 64, "retrieval_policy_sha256": "d" * 64, "tool_config_sha256": "e" * 64, "sandbox_config_sha256": "f" * 64, "analysis_script_sha256": "1" * 64, "experiment_arm_id": "adaptive-acquisition"},
        provider_call_ceiling=24, provider_token_ceiling=100000, one_shot_frozen=True,
    )


if __name__ == "__main__":
    result = admit(synthetic_config())
    print(json.dumps({"protocol": "e1b-v10-7-experiment-admission-offline-preflight-v1", "synthetic_admission": result, "provider_calls": 0, "live_runner_exists": False, "exact_command_authorized": False}, ensure_ascii=False, indent=2))
