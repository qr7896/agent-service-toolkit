import hashlib
import json
import sys

from evals import e1c_materialize
from evals.e1c_materialize import _field, _rank


def test_task_yaml_fields_and_rank_are_deterministic():
    text = "instance_id: a__b-1\nrepo: a/b\nbase_commit: abc123\nversion: '1.0'\n"
    assert _field(text, "repo") == "a/b"
    assert _field(text, "base_commit") == "abc123"
    assert _field(text, "version") == "1.0"
    assert _rank("a__b-1", "a/b", "abc123") == _rank("a__b-1", "a/b", "abc123")


def test_select_uses_frozen_tree_and_excludes_duplicate_base(tmp_path, monkeypatch):
    source_sha = "a" * 40
    base = "b" * 40
    names = ("owner__repo-1", "owner__repo-2", "owner__repo-3")
    blobs = {}
    tree = []
    for name in names:
        commit = "c" * 40 if name.endswith("-3") else base
        yaml = f"datasets:\n- SWE-bench/SWE-bench_Verified\nrepo: owner/repo\nbase_commit: {commit}\nversion: '1'\n".encode()
        for filename in e1c_materialize.REQUIRED_FILES:
            path = f"tasks/{name}/{filename}"
            data = yaml if filename == "task.yaml" else (
                json.dumps({"FAIL_TO_PASS": ["a"], "PASS_TO_PASS": [] if name.endswith("-3") else ["b"]}).encode()
                if filename == "tests.json" else filename.encode()
            )
            blobs[path] = data
            tree.append({"path": path, "type": "blob", "sha": e1c_materialize._git_blob_sha(data)})
    tree_path = tmp_path / "tree.json"
    tree_path.write_text(json.dumps({"sha": source_sha, "truncated": False, "tree": tree}), encoding="utf-8")
    monkeypatch.setattr(e1c_materialize, "OUT", tmp_path / "out")
    monkeypatch.setattr(e1c_materialize, "_get", lambda url: blobs[url.rsplit(f"/{source_sha}/", 1)[1]])

    selected = e1c_materialize.select(tree_path, target=2)

    assert len(selected) == 1
    assert selected[0]["selection_status"] == "selected_not_admitted"
    assert selected[0]["source_identity"].startswith(f"SWE-bench/swe-bench-tasks@{source_sha}:")
    assert selected[0]["task_metadata_sha256"] == hashlib.sha256(
        blobs[f"tasks/{selected[0]['instance_id']}/task.yaml"]
    ).hexdigest()


def test_replacement_materialization_keeps_original_inventory(tmp_path, monkeypatch):
    monkeypatch.setattr(e1c_materialize, "OUT", tmp_path)
    (tmp_path / "task_inventory.json").write_text("original", encoding="utf-8")
    (tmp_path / "candidate_manifest.json").write_text(json.dumps({"source_tree_sha": "a" * 40}), encoding="utf-8")
    (tmp_path / "cohort_preparation_status.json").write_text(json.dumps({
        "selection_mode": "network_bounded", "replacement_pool_partial": False,
        "replacement_pool": [{"instance_id": "replacement"}],
    }), encoding="utf-8")
    tree = tmp_path / "tree.json"
    tree.write_text(json.dumps({"sha": "a" * 40, "truncated": False}), encoding="utf-8")
    observed = []
    monkeypatch.setattr(e1c_materialize, "materialize", lambda rows, tree_path, name: observed.append((rows, tree_path, name)) or {"tasks": [{"materialization_status": "complete"}]})
    monkeypatch.setattr(sys, "argv", ["materialize", "--replacement-pool", "--tree", str(tree)])
    e1c_materialize.main()
    assert observed[0][2] == "replacement_task_inventory.json"
    assert (tmp_path / "task_inventory.json").read_text(encoding="utf-8") == "original"


def test_select_cache_only_skips_missing_metadata_without_network(tmp_path, monkeypatch):
    source_sha = "a" * 40
    tree_path = tmp_path / "tree.json"
    tree_path.write_text(json.dumps({
        "sha": source_sha,
        "truncated": False,
        "tree": [{"path": "tasks/owner__repo-1/task.yaml", "type": "blob", "sha": "b" * 40}],
    }), encoding="utf-8")
    monkeypatch.setattr(e1c_materialize, "OUT", tmp_path / "out")
    monkeypatch.setattr(e1c_materialize, "_get", lambda url: (_ for _ in ()).throw(AssertionError("network used")))
    assert e1c_materialize.select(tree_path, target=1, cache_only=True) == []
