import json

import pytest
import yaml

from evals import e1c_admission
from evals.e1c_admission import _official_grader, source_identity


def test_pinned_official_grader_smoke():
    _, test_maintained, test_passed, resolve_case, _ = _official_grader()
    assert test_passed("case", {"case": "PASSED"})
    assert not test_passed("case", {"case": "SKIPPED"})
    assert test_maintained("case", {"case": "SKIPPED"})
    assert resolve_case("case", {"case": "FAILED"}) == "case"


def test_setup_only_image_diff_requires_disjoint_patches(tmp_path):
    patch = tmp_path / "gold.patch"
    patch.write_text("diff --git a/src/core.py b/src/core.py\n", encoding="utf-8")
    markers = (
        b"E1C_CONTAINER_HEAD:" + b"a" * 40 + b"\n"
        b"E1C_EXPECTED_TREE:" + b"b" * 40 + b"\n"
        b"E1C_ACTUAL_TREE:" + b"c" * 40 + b"\n"
        b"E1C_IMAGE_DIFF_PATH:setup.py\nE1C_IMAGE_DIFF_PATH:tox.ini\n"
    )
    assert source_identity(markers, (patch,))["source_identity_valid"] is True
    patch.write_text("diff --git a/setup.py b/setup.py\n", encoding="utf-8")
    assert source_identity(markers, (patch,))["source_identity_valid"] is False
    patch.write_text("diff --git a/src/core.py b/src/core.py\n", encoding="utf-8")
    assert source_identity(markers + b"E1C_IMAGE_DIFF_PATH:src/core.py\n", (patch,))["source_identity_valid"] is False


def test_probe_allows_empty_pass_to_pass_before_docker(tmp_path, monkeypatch):
    instance_id = "django__django-16092"
    task_dir = tmp_path / instance_id
    task_dir.mkdir()
    (task_dir / "task.yaml").write_text(
        yaml.safe_dump(
            {
                "instance_id": instance_id,
                "base_commit": "a" * 40,
                "image": "swebench/example:latest",
                "repo": "django/django",
                "version": "4.1",
                "log_parser": "parse_log_django",
            }
        ),
        encoding="utf-8",
    )
    (task_dir / "tests.json").write_text(
        json.dumps({"FAIL_TO_PASS": ["case"], "PASS_TO_PASS": []}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        e1c_admission.subprocess,
        "check_output",
        lambda *args, **kwargs: (
            "swebench/example@sha256:" + "b" * 64
        ),
    )
    monkeypatch.setattr(
        e1c_admission,
        "_official_grader",
        lambda: pytest.fail("empty P2P should pass metadata validation"),
    )
    with pytest.raises(pytest.fail.Exception):
        e1c_admission.probe(
            instance_id,
            "base",
            task_root=tmp_path,
            artifact_root=tmp_path / "artifacts",
        )
