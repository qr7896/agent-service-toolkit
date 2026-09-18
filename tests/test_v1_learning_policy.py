import json
from pathlib import Path

from evals.v1_evaluate_frozen import sha256, verify_manifest
from evals.v1_train_ranker import PRE_ACTION_FEATURES
from evals.v1_train_stopper import STATE_FEATURES, choose_threshold


def test_ranker_runtime_features_are_pre_action_only():
    assert all(not f.startswith("candidate_output_") for f in PRE_ACTION_FEATURES)
    assert all(not f.startswith("candidate_new_") for f in PRE_ACTION_FEATURES)
    assert "candidate_redundancy" not in PRE_ACTION_FEATURES


def test_stopper_has_no_candidate_features():
    assert all(not f.startswith("candidate_") for f in STATE_FEATURES)


def test_metrics_keep_test_frozen():
    rank = json.loads(Path("evals/results/v1_ranker_metrics.json").read_text(encoding="utf-8"))
    stop = json.loads(Path("evals/results/v1_stopper_metrics.json").read_text(encoding="utf-8"))
    assert rank["test_status"] == "frozen_not_evaluated"
    assert stop["test_status"] == "frozen_not_evaluated"
    assert "test" not in rank["models"]["logreg"]
    assert "test" not in stop


def test_manifest_mismatch_is_detected(tmp_path):
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"changed")
    manifest = {"files": {str(artifact): "0" * 64}}
    mismatches = verify_manifest(manifest)
    assert len(mismatches) == 1
    assert mismatches[0]["path"] == str(artifact)


def test_manifest_text_hash_is_newline_portable(tmp_path):
    windows_file = tmp_path / "artifact.json"
    linux_file = tmp_path / "artifact-copy.json"
    windows_file.write_bytes(b'{\r\n  "frozen": true\r\n}\r\n')
    linux_file.write_bytes(b'{\n  "frozen": true\n}\n')
    assert sha256(windows_file) == sha256(linux_file)


def test_stop_threshold_tie_break_is_safety_conservative():
    class Model:
        def predict_proba(self, x):
            import numpy as np

            return np.asarray([[0.8, 0.2], [0.2, 0.8]])

    rows = [{"x": [0.0], "y": 0}, {"x": [1.0], "y": 1}]
    assert choose_threshold(Model(), rows) == 0.8


def test_fair_baseline_uses_train_only_unseen_cluster_fallback():
    report = json.loads(
        Path("evals/results/v1_matched_v0_utility.json").read_text(encoding="utf-8")
    )
    assert report["train_tasks_for_prior"] == 12
    assert report["prior_coverage"] == 0.0
    assert report["fallback_count"] == report["tasks"] == 4
    assert not (set(report["test_clusters"]) & set(report["prior_map"]))
    assert (
        report["evidence_gate"]["summary"]["context_recall"]
        == report["utility_gate_groupaware"]["summary"]["context_recall"]
    )


def test_fair_comparator_uses_exact_ids_and_medians():
    report = json.loads(Path("evals/results/v1_go_no_go.json").read_text(encoding="utf-8"))
    assert len(report["task_ids"]) == 4
    assert report["prior_coverage"] == 0.0 and report["fallback_count"] == 4
    assert report["delta"]["median_context_tokens"]["reduction_pct"] == 35.32
    assert report["delta"]["median_tool_calls"]["reduction_pct"] == 50.0
    assert report["go_no_go"]["median_cost_reduction_at_least_10pct"] is True
