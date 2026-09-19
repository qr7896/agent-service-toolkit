from evals.v2_dataset import canonical_record_sha256, validate_records
from evals.v2_offline_collector import collect_deterministic_record


def row(task="t1", step=0, split="train", cluster="c1", commit="a"):
    return collect_deterministic_record(
        task, step,
        {"split": split, "cluster": cluster, "source_commit": commit},
        ["lexical", "structural", "stop"],
        "lexical",
        {"lexical": 1.0},
    ).to_dict()


def test_dataset_below_200_is_not_replay_ready():
    summary = validate_records([row()], min_records=200)
    assert summary["errors"] == []
    assert summary["ready_for_replay"] is False


def test_dataset_detects_duplicate_task_step_and_hash():
    r = row()
    summary = validate_records([r, r], min_records=1)
    assert summary["duplicate_hashes"] == 1
    assert any("duplicate task-step" in error for error in summary["errors"])


def test_dataset_detects_runtime_gold_leakage():
    r = row()
    r["state"]["oracle_gain"] = 1
    assert any("runtime leakage" in error for error in validate_records([r], min_records=1)["errors"])


def test_dataset_detects_cross_split_cluster_and_commit():
    rows = [row("a", 0, "train", "same", "same"), row("b", 0, "test", "same", "same")]
    summary = validate_records(rows, min_records=1)
    assert summary["cross_split_clusters"] == ["same"]
    assert summary["cross_split_commits"] == ["same"]


def test_dataset_rejects_unsafe_action():
    r = row()
    r["candidates"][0]["action"] = "shell"
    assert any("unsafe" in error for error in validate_records([r], min_records=1)["errors"])


def test_canonical_hash_is_order_stable():
    r = row()
    reordered = dict(reversed(list(r.items())))
    assert canonical_record_sha256(r) == canonical_record_sha256(reordered)


def test_valid_200_record_dataset_is_replay_ready():
    rows = [
        row(task=f"task-{i // 4}", step=i % 4, split="train", cluster=f"c-{i // 4}", commit=f"k-{i // 4}")
        for i in range(200)
    ]
    summary = validate_records(rows)
    assert summary["records"] == 200
    assert summary["tasks"] == 50
    assert summary["ready_for_replay"] is True
    assert summary["errors"] == []
