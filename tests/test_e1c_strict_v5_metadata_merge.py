import json

import pytest

from evals.e1c_strict_v5_metadata_merge import merge


def _write(path, source_name, revision, tasks):
    path.write_text(json.dumps({
        "source_name": source_name,
        "source_revision": revision,
        "tasks": tasks,
    }), encoding="utf-8")


def test_partial_sources_merge_with_field_provenance(tmp_path) -> None:
    identity = tmp_path / "identity.json"
    commit = tmp_path / "commit.json"
    image = tmp_path / "image.json"
    _write(identity, "identity", "r1", [
        {"instance_id": "unseen-aa", "repo": "owner/repo"},
        {"instance_id": "unseen-bb", "repo": "owner/repo"},
        {"instance_id": "unseen-cc", "repo": "owner/repo"},
    ])
    _write(commit, "commit", "r2", [
        {"instance_id": "unseen-aa", "base_commit": "a" * 40},
        {"instance_id": "unseen-bb", "base_commit": "b" * 40},
        {"instance_id": "unseen-cc", "base_commit": "c" * 40},
    ])
    _write(image, "image", "r3", [
        {"instance_id": "unseen-aa", "image": "img:a"},
        {"instance_id": "unseen-bb", "image": "img:b"},
        {"instance_id": "unseen-cc", "image": "img:c"},
    ])
    result = merge([identity, commit, image])
    assert result["complete_count"] == 3
    assert result["eligible_count"] == 3
    assert result["field_provenance"]["unseen-aa"]["base_commit"]["source_revision"] == "r2"


def test_partial_source_conflict_fails_closed(tmp_path) -> None:
    left = tmp_path / "left.json"
    right = tmp_path / "right.json"
    _write(left, "left", "r1", [{"instance_id": "x", "repo": "a/b"}])
    _write(right, "right", "r2", [{"instance_id": "x", "repo": "c/d"}])
    with pytest.raises(ValueError, match="conflicting metadata"):
        merge([left, right])


def test_partial_source_forbidden_content_fails_closed(tmp_path) -> None:
    source = tmp_path / "source.json"
    _write(source, "bad", "r1", [{
        "instance_id": "x",
        "repo": "a/b",
        "problem_statement": "forbidden",
    }])
    with pytest.raises(ValueError, match="forbidden"):
        merge([source])
