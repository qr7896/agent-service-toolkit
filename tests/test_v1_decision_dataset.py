from types import SimpleNamespace

from evals.v1_decision_dataset import (
    GOLD_ONLY_FIELDS,
    V1_CLUSTER_SPLIT,
    _v1_split,
    validate_episodes,
)


def test_runtime_features_have_no_gold_leakage():
    eps = [
        {
            "instance_id": "a",
            "split": "train",
            "cluster": "c1",
            "stop_label": True,
            "candidates": [{"features": {"round": 0, "candidate_cost": 1.0}}],
        }
    ]
    out = validate_episodes(eps)
    assert out["runtime_gold_leakage"] == []
    assert out["cross_split_clusters"] == []
    assert out["cross_split_commits"] == []


def test_gold_leakage_is_detected():
    eps = [
        {
            "instance_id": "a",
            "split": "train",
            "cluster": "c1",
            "stop_label": False,
            "candidates": [{"features": {"gold_files": 1}}],
        }
    ]
    assert validate_episodes(eps)["runtime_gold_leakage"] == ["gold_files"]


def test_cluster_split_leakage_is_detected():
    eps = [
        {
            "instance_id": "a",
            "split": "train",
            "cluster": "same",
            "stop_label": True,
            "candidates": [],
        },
        {
            "instance_id": "b",
            "split": "test",
            "cluster": "same",
            "stop_label": True,
            "candidates": [],
        },
    ]
    assert validate_episodes(eps)["cross_split_clusters"] == ["same"]


def test_commit_split_leakage_is_detected():
    eps = [
        {
            "instance_id": "a",
            "split": "train",
            "cluster": "c1",
            "source_commit": "same",
            "stop_label": True,
            "candidates": [],
        },
        {
            "instance_id": "b",
            "split": "test",
            "cluster": "c2",
            "source_commit": "same",
            "stop_label": True,
            "candidates": [],
        },
    ]
    assert validate_episodes(eps)["cross_split_commits"] == ["same"]


def test_oracle_fields_are_label_only():
    assert "oracle_gain" in GOLD_ONLY_FIELDS and "stop_label" in GOLD_ONLY_FIELDS


def test_v1_cluster_split_is_group_disjoint():
    assert set(V1_CLUSTER_SPLIT.values()) == {"train", "dev", "test"}
    assert _v1_split(SimpleNamespace(cluster="validation")) == "train"
    assert _v1_split(SimpleNamespace(cluster="memory-quality")) == "dev"
    assert _v1_split(SimpleNamespace(cluster="sandbox-output")) == "test"
