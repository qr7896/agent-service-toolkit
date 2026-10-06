import hashlib
import json
import subprocess

import pytest

from evals.e1c_evaluation_2_fallback_control import derive_control


def context(tmp_path):
    code = "def api(labels):\n    if len(labels) != 3:\n        raise ValueError('shape')\n    return labels\n"
    (tmp_path / "core.py").write_bytes(code.encode())
    for args in (["init", "-q"], ["add", "core.py"],
                 ["-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"]):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    commit = subprocess.check_output(["git", "-C", str(tmp_path), "rev-parse", "HEAD"], text=True).strip()
    issue = "The public API should accept array labels."
    return {"issue": issue, "base_commit": commit, "input_sha256": "a" * 64, "candidate_paths": ["core.py"],
            "windows": [{"path": "core.py", "source_sha256": hashlib.sha256(code.encode()).hexdigest()}]}


def probe(body):
    return {"source": "import numpy as np\nfrom core import api\n" + body,
            "issue_quote": "should accept array labels"}


def test_same_values_length_and_target_are_preserved(tmp_path):
    frozen = context(tmp_path)
    candidate = probe("labels = np.array(['a','b','c'])\napi(labels)\ndone = True\nassert done")
    original = dict(candidate)
    control, proof = derive_control(candidate, frozen, tmp_path)
    assert "api(['a', 'b', 'c'])" in control["source"]
    assert proof["contrast"]["literal_length"] == 3 and candidate == original
    assert proof["compiled"] and not proof["preconditions_verified"]
    assert not proof["semantic_equivalence_proven"] and not proof["trusted_reproducer"]


def test_invalid_dimensions_are_not_repaired_to_make_control_pass(tmp_path):
    frozen = context(tmp_path)
    control, proof = derive_control(probe("api(np.array(['only_one']))\nassert result == 0"), frozen, tmp_path)
    assert "api(['only_one'])" in control["source"]
    assert proof["contrast"]["literal_length"] == 1


@pytest.mark.parametrize("mutation", ["labels[0] = 'x'", "labels.sort()", "custom(labels)",
                                      "np.array = custom", "labels = custom"])
def test_mutation_escape_and_shadowing_are_unknown(tmp_path, mutation):
    frozen = context(tmp_path)
    control, proof = derive_control(probe("labels = np.array(['a','b','c'])\n" + mutation
                                         + "\napi(labels)\nassert result == 0"), frozen, tmp_path)
    assert control is None and not proof["compiled"]


@pytest.mark.parametrize("body", ["api(np.array(['a']))\nassert True",
                                  "def check():\n    api(np.array(['a']))\n    assert True\ncheck()",
                                  "api(np.array(['a']))\nassert False"])
def test_constant_oracle_never_qualifies(tmp_path, body):
    control, proof = derive_control(probe(body), context(tmp_path), tmp_path)
    assert control is None and proof["status"] == "constant_oracle_rejected"


def test_two_array_arguments_cannot_be_isolated(tmp_path):
    control, proof = derive_control(probe("api(np.array(['a']), np.array(['b']))\nassert result == 0"),
                                    context(tmp_path), tmp_path)
    assert control is None and proof["status"] == "ambiguous_contrast"


@pytest.mark.parametrize("body", ["def check():\n    api(np.array(['a']))\n    assert result == 0\ncheck()",
                                  "api(np.array(['a']))\nresult = custom()\nassert result == 0",
                                  "api(np.array([x for x in values]))\nassert result == 0",
                                  "other(np.array(['a']))\nassert result == 0"])
def test_unknown_execution_or_production_call_is_not_guessed(tmp_path, body):
    control, proof = derive_control(probe(body), context(tmp_path), tmp_path)
    assert control is None and not proof["compiled"]


def test_source_hash_change_fails_closed(tmp_path):
    frozen = context(tmp_path)
    (tmp_path / "core.py").write_bytes(b"def api(labels): return labels\n")
    with pytest.raises(ValueError, match="production source changed"):
        derive_control(probe("api(np.array(['a']))\nassert result == 0"), frozen, tmp_path)


def test_rebound_callee_is_not_a_production_proof(tmp_path):
    control, proof = derive_control(probe("api = custom\napi(np.array(['a']))\nassert result == 0"),
                                    context(tmp_path), tmp_path)
    assert control is None and proof["status"] == "callee_binding_unproven"


def test_audit_cannot_reuse_existing_namespace(tmp_path, monkeypatch):
    from evals import e1c_evaluation_2_fallback_control_audit as runner

    monkeypatch.setattr(runner, "OUT", tmp_path)
    with pytest.raises(FileExistsError, match="do not retry"):
        runner.audit()


def test_audit_rejects_previous_freeze_change_before_engine(tmp_path, monkeypatch):
    from evals import e1c_evaluation_2_fallback_control_audit as runner

    monkeypatch.setattr(runner, "OUT", tmp_path / "new-run")
    monkeypatch.setattr(runner, "_sha", lambda _: "changed")
    with pytest.raises(ValueError, match="previous frozen V4 records differ"):
        runner.audit()
    assert not runner.OUT.exists()


def test_audit_binds_file_digest_not_canonical_payload_digest(tmp_path, monkeypatch):
    from evals import e1c_evaluation_2_fallback_control_audit as runner

    previous = tmp_path / "previous"
    (previous / "inputs").mkdir(parents=True)
    tasks = []
    image = "sha256:" + "b" * 64
    for n in range(9):
        iid = f"synthetic-{n}"
        path = previous / "inputs" / f"{iid}.json"
        path.write_text(json.dumps({"input_sha256": "a" * 64, "windows": []}), encoding="utf-8")
        tasks.append({"instance_id": iid, "input_sha256": runner._sha(path), "image_id": image})
        assert runner._sha(path) != "a" * 64
    (previous / "freeze.json").write_text(json.dumps({"fixed_denominator": 12, "tasks": tasks}), encoding="utf-8")
    monkeypatch.setattr(runner, "PREVIOUS", previous)
    monkeypatch.setattr(runner, "OUT", tmp_path / "new")
    monkeypatch.setattr(runner, "PINNED", {})
    monkeypatch.setattr(runner, "verify_workspace", lambda *_: None)
    monkeypatch.setattr(runner, "verified_local_image", lambda _: image)
    engines = []
    monkeypatch.setattr(runner, "require_engine", lambda images: engines.append(images))
    monkeypatch.setattr(runner, "execute_candidate", lambda *_a, **_k: pytest.fail("no candidate may execute"))
    result = runner.audit()
    assert result["audited_tasks"] == 9 and result["A_candidates"] == 0 and len(engines) == 1
    assert result["provider_calls"] == result["gold_reads"] == result["trusted_reproducer_count"] == 0
    assert result["previous_records_unchanged"] and (runner.OUT / "freeze.json").exists()
