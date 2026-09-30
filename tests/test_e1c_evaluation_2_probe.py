import hashlib
import json
import subprocess
from types import SimpleNamespace

import pytest

from evals import e1c_evaluation_2_metadata as metadata
from evals import e1c_evaluation_2_probe as probe
from evals.e1c_evaluation_2_probe import (
    docker_command,
    execute_candidate,
    feedback_prompt,
    freeze_input,
    generation_views,
    issue_missing_optional_import,
    validate_candidate,
)


def test_issue_only_input_and_offline_probe_guard(tmp_path, monkeypatch):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "engine.py").write_text("def normalize_value(value):\n    return value\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_engine.py").write_text("assert normalize_value(3) == 4\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "pkg/engine.py", "tests/test_engine.py"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "-c", "user.name=E1C Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "frozen base"],
        check=True,
    )
    base_commit = subprocess.check_output(["git", "-C", str(tmp_path), "rev-parse", "HEAD"], text=True).strip()
    issue = "normalize_value should return 4 for input 3.\nassert normalize_value(3) == 4"
    frozen = freeze_input(issue, tmp_path, base_commit)
    assert frozen["candidate_count"] > 0
    assert all(not path.startswith("tests/") for path in frozen["candidate_paths"])
    assert "assert normalize_value" not in frozen["issue"]
    views = generation_views(frozen)
    assert [view["view"] for view in views] == ["behavior_expected", "api_usage"]
    assert all("test_engine.py" not in view["prompt"] for view in views)
    with pytest.raises(ValueError, match="exact frozen base"):
        freeze_input(issue, tmp_path, "a" * 40)
    with pytest.raises(RuntimeError, match="evaluator sentinel"):
        freeze_input(issue, tmp_path, base_commit, forbidden_values=("normalize_value",))
    (pkg / "engine.py").write_text("def normalize_value(value):\n    return 4\n", encoding="utf-8")
    with pytest.raises(ValueError, match="exact frozen base"):
        freeze_input(issue, tmp_path, base_commit)
    (pkg / "engine.py").write_text("def normalize_value(value):\n    return value\n", encoding="utf-8")
    source = "from pkg.engine import normalize_value\nassert normalize_value(3) == 4\n"
    candidate = validate_candidate(source, "normalize_value should return 4", frozen)
    assert candidate["trusted_reproducer"] is False
    mounted = tmp_path / "probe.py"
    mounted.write_bytes(source.encode("utf-8"))
    image = "swebench/sweb.eval.x86_64.pkg_1776_pkg-1@sha256:" + "b" * 64
    command = docker_command(candidate, image, base_commit, mounted)
    assert "--pull=never" in command and "none" in command and "--read-only" in command
    assert "PYTHONPATH=/testbed/src:/testbed" in command
    assert "/opt/miniconda3/envs/testbed/bin/python -X utf8" in command[-3]
    assert "git -C /testbed diff --raw --no-abbrev --no-renames" in command[-3]
    assert '$3 != $4' in command[-3]
    assert '$1 != ":100644"' in command[-3]
    assert "git -C /testbed merge-base --is-ancestor" in command[-3]
    assert hashlib.sha256(mounted.read_bytes()).hexdigest() == candidate["probe_sha256"]

    with pytest.raises(ValueError, match="forbidden module"):
        validate_candidate("import os\nassert True", "normalize_value should return 4", frozen)
    with pytest.raises(ValueError, match="outside frozen"):
        validate_candidate("from other import x\nassert x", "normalize_value should return 4", frozen)
    validate_candidate("import json\nimport warnings\nimport numpy as np\nassert np is not None", "normalize_value should return 4", frozen)
    with pytest.raises(ValueError, match="evidence"):
        validate_candidate(source, "invented obligation", frozen)
    with pytest.raises(ValueError, match="does not match"):
        docker_command({**candidate, "probe_sha256": "c" * 64}, image, base_commit, mounted)

    def fake_docker(command, *, stdout, stderr, timeout, check):
        assert "--pull=never" in command and "none" in command
        stdout.write(b"AssertionError: behavior mismatch\n")
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(probe.subprocess, "run", fake_docker)
    execution = execute_candidate(candidate, image, base_commit, tmp_path / "runs")
    assert len(execution["runs"]) == 2
    assert execution["repeatable_failure_candidate"] is True
    assert execution["trusted_reproducer"] is False

    def fake_setup_error(command, *, stdout, stderr, timeout, check):
        stdout.write(b"ModuleNotFoundError: missing environment dependency\n")
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(probe.subprocess, "run", fake_setup_error)
    blocked = execute_candidate(candidate, image, base_commit, tmp_path / "setup_failure")
    assert len(blocked["runs"]) == 1
    assert blocked["repeatable_failure_candidate"] is False

    def fake_unclassified(command, *, stdout, stderr, timeout, check):
        stdout.write(b"marshmallow.exceptions.ValidationError: invalid datetime\n")
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(probe.subprocess, "run", fake_unclassified)
    diagnostic = execute_candidate(
        candidate, image, base_commit, tmp_path / "unclassified", repeat_nonsetup_failure=True
    )
    assert diagnostic["repeatable_nonsetup_failure"] is True
    assert diagnostic["repeatable_failure_candidate"] is False


def test_balanced_input_keeps_issue_lexical_window_when_explicit_path_has_many_definitions(tmp_path):
    package = tmp_path / "pkg"
    package.mkdir()
    source = "\n".join(
        [f"def alpha_{index}():\n    return {index}\n" for index in range(8)]
        + ["def omega():\n    marker_special_case = 99\n    return marker_special_case\n"]
    )
    (package / "engine.py").write_text(source, encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "pkg/engine.py"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "-c", "user.name=E1C Test", "-c", "user.email=test@example.invalid",
         "commit", "-qm", "frozen base"],
        check=True,
    )
    base = subprocess.check_output(["git", "-C", str(tmp_path), "rev-parse", "HEAD"], text=True).strip()
    issue = "pkg/engine.py marker_special_case should return a different value."
    old = freeze_input(issue, tmp_path, base)
    balanced = freeze_input(issue, tmp_path, base, balanced=True)
    assert old["schema"].endswith("v2") and balanced["schema"].endswith("v3")
    assert not any("marker_special_case = 99" in row["text"] for row in old["windows"])
    assert any("marker_special_case = 99" in row["text"] for row in balanced["windows"])
    assert any(row["origin"] == "issue_lexical" for row in balanced["windows"])


def test_feedback_prompt_uses_only_issue_source_and_base_pass_signal():
    frozen = {
        "schema": "e1c-evaluation-2-probe-input-v3", "status": "ready_for_generation",
        "issue": "Public API should return one.",
        "windows": [{"path": "pkg/engine.py", "text": "def public_api(): return 0"}],
    }
    prompt = feedback_prompt(frozen, "from pkg.engine import public_api\nassert public_api() == 0")
    assert "exit_0_no_prepatch_failure" in prompt
    assert "Public API should return one." in prompt
    assert "grader" not in prompt.lower()
    with pytest.raises(ValueError, match="balanced"):
        feedback_prompt({**frozen, "schema": "e1c-evaluation-2-probe-input-v2"}, "assert True")


def test_issue_only_optional_dependency_isolation(tmp_path):
    frozen = {
        "issue": "With `python-sampledep` _not_ installed, parsing should work.",
        "windows": [{"text": "try:\n    from sampledep import parser\nexcept ImportError:\n    parser = None"}],
    }
    assert issue_missing_optional_import(frozen) == "sampledep"
    assert issue_missing_optional_import({**frozen, "issue": "Parsing should work."}) is None
    source = "import pkg\nassert pkg.value == 1\n"
    mounted = tmp_path / "probe.py"
    mounted.write_bytes(source.encode("utf-8"))
    blocker_dir = tmp_path / "optional_missing"
    blocker_dir.mkdir()
    (blocker_dir / "sampledep.py").write_text("raise ModuleNotFoundError('sampledep')\n", encoding="utf-8")
    candidate = {"probe_sha256": hashlib.sha256(source.encode()).hexdigest()}
    image = "swebench/sweb.eval.x86_64.pkg_1776_pkg-1@sha256:" + "b" * 64
    command = docker_command(candidate, image, "a" * 40, mounted, blocked_import_dir=blocker_dir)
    assert "PYTHONPATH=/e1c2_optional_missing:/testbed/src:/testbed" in command
    assert any("target=/e1c2_optional_missing,readonly" in part for part in command)
    assert "--network" in command and "none" in command


def test_dev12_metadata_fetch_stays_identity_bound(monkeypatch, tmp_path):
    identity = metadata.IDENTITY.read_bytes()

    def fake_fetch(row, revision):
        assert revision == "3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d"
        return {
            "instance_id": row["instance_id"],
            "repo": "example/repo",
            "base_commit": "a" * 40,
            "image": "swebench/example:latest",
        }

    monkeypatch.setattr(metadata, "fetch_task_metadata", fake_fetch)
    output = tmp_path / "metadata.json"
    result = metadata.acquire(identity, output)
    assert len(result["tasks"]) == 12
    assert result["provider_calls"] == 0
    assert output.is_file()


def test_mirror_runtime_reference_requires_frozen_ledger(monkeypatch, tmp_path):
    identity = json.loads(probe.IDENTITY.read_bytes())
    tasks = [
        {"instance_id": item["instance_id"], "image": f"swebench/sweb.eval.x86_64.example-{n}:latest"}
        for n, item in enumerate(identity["tasks"])
    ]
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps({"tasks": tasks}), encoding="utf-8")
    digest = "sha256:" + "b" * 64
    rows = [
        {
            "instance_id": item["instance_id"], "official_image": item["image"],
            "digest_identical": True,
            "official": {"top_digest": digest, "platform_digest": digest},
            "mirror": {"top_digest": digest, "platform_digest": digest},
        }
        for item in tasks
    ]
    transport_path = tmp_path / "transport.json"
    transport_path.write_text(json.dumps({
        "mirror_host": "docker.1panel.live", "digest_identical_count": 12,
        "metadata_sha256": hashlib.sha256(metadata_path.read_bytes()).hexdigest(),
        "identity_sha256": hashlib.sha256(probe.IDENTITY.read_bytes()).hexdigest(),
        "rows": rows,
    }), encoding="utf-8")
    monkeypatch.setattr(probe, "METADATA", metadata_path)
    monkeypatch.setattr(probe, "_TRANSPORT", transport_path)
    monkeypatch.setattr(probe, "_TRANSPORT_SHA256", hashlib.sha256(transport_path.read_bytes()).hexdigest())
    reference = probe.verified_mirror_image(tasks[0]["instance_id"])
    assert reference == f"docker.1panel.live/{tasks[0]['image'].removesuffix(':latest')}@{digest}"
    acquire = tmp_path / "acquire"
    loaded = acquire / tasks[0]["instance_id"] / "loaded.json"
    loaded.parent.mkdir(parents=True)
    image_id = "sha256:" + "c" * 64
    status = {
        "schema": "e1c-evaluation-2-verified-mirror-acquisition-v1",
        "instance_id": tasks[0]["instance_id"],
        "top_digest": digest, "platform_digest": digest,
        "config_digest": image_id, "verified_blob_count": 2,
        "load": {"loaded_config_digest": image_id},
        "provider_calls": 0, "proxy_bypassed": True,
    }
    rows[0]["official"]["layer_count"] = 1
    transport_path.write_text(json.dumps({
        "mirror_host": "docker.1panel.live", "digest_identical_count": 12,
        "metadata_sha256": hashlib.sha256(metadata_path.read_bytes()).hexdigest(),
        "identity_sha256": hashlib.sha256(probe.IDENTITY.read_bytes()).hexdigest(),
        "rows": rows,
    }), encoding="utf-8")
    monkeypatch.setattr(probe, "_TRANSPORT_SHA256", hashlib.sha256(transport_path.read_bytes()).hexdigest())
    loaded.write_text(json.dumps(status), encoding="utf-8")
    monkeypatch.setattr(probe, "_ACQUIRE", acquire)
    assert probe.verified_local_image(tasks[0]["instance_id"]) == image_id
    source = b"assert False\n"
    mounted = tmp_path / "probe.py"
    mounted.write_bytes(source)
    candidate = {"probe_sha256": hashlib.sha256(source).hexdigest()}
    assert docker_command(candidate, reference, "a" * 40, mounted)[-6] == reference
    assert docker_command(candidate, image_id, "a" * 40, mounted)[-6] == image_id
    status["platform_digest"] = "sha256:" + "d" * 64
    loaded.write_text(json.dumps(status), encoding="utf-8")
    with pytest.raises(ValueError, match="local image"):
        docker_command(candidate, image_id, "a" * 40, mounted)
    alternate = tmp_path / "transport_1ms.json"
    alternate.write_text(transport_path.read_text(encoding="utf-8").replace("docker.1panel.live", "docker.1ms.run"), encoding="utf-8")
    monkeypatch.setattr(probe, "_TRANSPORT_ALT", alternate)
    monkeypatch.setattr(probe, "_TRANSPORT_ALT_SHA256", hashlib.sha256(alternate.read_bytes()).hexdigest())
    alternate_reference = probe.verified_mirror_image(tasks[0]["instance_id"], "docker.1ms.run")
    assert docker_command(candidate, alternate_reference, "a" * 40, mounted)[-6] == alternate_reference
    transport_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="ledger changed"):
        probe.verified_mirror_image(tasks[0]["instance_id"])


def test_issue_only_localizer_skips_oracle_marked_source_window(tmp_path, monkeypatch):
    source = tmp_path / "engine.py"
    source.write_text("def behavior():\n    return 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "engine.py"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "-c", "user.name=E1C Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "base"],
        check=True,
    )
    base = subprocess.check_output(["git", "-C", str(tmp_path), "rev-parse", "HEAD"], text=True).strip()
    common = {"path": "engine.py", "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    monkeypatch.setattr(probe, "structural_windows", lambda *_args, **_kwargs: [
        {**common, "symbol": "color", "start_line": 1, "end_line": 1, "origin": "definition", "text": "golden color"},
        {**common, "symbol": "behavior", "start_line": 2, "end_line": 2, "origin": "definition", "text": "return 1"},
    ])
    monkeypatch.setattr(probe, "lexical_windows", lambda *_args, **_kwargs: [])
    frozen = freeze_input("Behavior should return one.", tmp_path, base)
    assert frozen["candidate_count"] == 1
    assert frozen["oracle_filtered_window_count"] == 1
    assert frozen["windows"][0]["symbol"] == "behavior"
    assert "golden" not in generation_views(frozen)[0]["prompt"]


def test_candidate_imports_exact_base_local_public_package_only(tmp_path):
    for package in ("acme", "pytest"):
        folder = tmp_path / "src" / package
        folder.mkdir(parents=True)
        (folder / "__init__.py").write_text("value = 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "src"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "-c", "user.name=E1C Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "base"],
        check=True,
    )
    base = subprocess.check_output(["git", "-C", str(tmp_path), "rev-parse", "HEAD"], text=True).strip()
    frozen = {
        "issue": "Public API should return one.", "base_commit": base,
        "candidate_paths": ["src/acme/__init__.py"], "input_sha256": "a" * 64,
    }
    candidate = validate_candidate("import acme\nimport pytest\nassert acme.value == 1\n", "Public API should return one", frozen, workspace=tmp_path)
    assert candidate["schema"] == "e1c-evaluation-2-candidate-v2"
    validate_candidate("import datetime\nimport acme\nassert datetime.date(2020, 1, 1).year == acme.value + 2019", "Public API should return one", frozen, workspace=tmp_path)
    with pytest.raises(ValueError, match="forbidden module"):
        validate_candidate("import pytest\nassert True", "Public API should return one", frozen)
    with pytest.raises(ValueError, match="outside frozen"):
        validate_candidate("import unrelated\nassert True", "Public API should return one", frozen, workspace=tmp_path)
    with pytest.raises(ValueError, match="forbidden module"):
        validate_candidate("import os\nassert True", "Public API should return one", frozen, workspace=tmp_path)
    (tmp_path / "src" / "acme" / "__init__.py").write_text("value = 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="clean frozen-base"):
        validate_candidate("import acme\nassert True", "Public API should return one", frozen, workspace=tmp_path)


def test_candidate_cannot_synthesize_expected_warning():
    frozen = {
        "issue": "Public API should emit a deprecation warning.",
        "candidate_paths": ["src/acme/__init__.py"],
        "input_sha256": "a" * 64,
    }
    with pytest.raises(ValueError, match="synthesizes its own expected warning"):
        validate_candidate(
            "import warnings\nwarnings.warn('deprecated')\nassert True\n",
            "Public API should emit a deprecation warning",
            frozen,
        )
