import evals.e1c_strict_v5_verification as verification


def test_missing_image_fails_closed_without_running_phases(tmp_path, monkeypatch) -> None:
    instance_id = "task-1"
    materialized = tmp_path / "materialized"
    grader = tmp_path / "grader"
    staging = tmp_path / "staging"
    (materialized / instance_id).mkdir(parents=True)
    (grader / instance_id).mkdir(parents=True)
    (materialized / instance_id / "task.yaml").write_text("instance_id: task-1\n", encoding="utf-8")
    for name in verification.FILES:
        (grader / instance_id / name).write_text(name, encoding="utf-8")
    monkeypatch.setattr(verification, "MATERIALIZED_ROOT", materialized)
    monkeypatch.setattr(verification, "GRADER_ROOT", grader)
    monkeypatch.setattr(verification, "STAGING_ROOT", staging)
    monkeypatch.setattr(verification, "_image_digest", lambda image: None)
    monkeypatch.setattr(
        verification,
        "_phase",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("phase must not run")),
    )
    result = verification.verify_task(instance_id, "image:latest")
    assert result["status"] == "official_image_unavailable"
    assert result["infrastructure_failure"] is True
    assert result["repair_visible"] is False


def test_verification_serializes_only_distilled_phase_evidence(tmp_path, monkeypatch) -> None:
    instance_id = "task-1"
    materialized = tmp_path / "materialized"
    grader = tmp_path / "grader"
    staging = tmp_path / "staging"
    (materialized / instance_id).mkdir(parents=True)
    (grader / instance_id).mkdir(parents=True)
    (materialized / instance_id / "task.yaml").write_text("instance_id: task-1\n", encoding="utf-8")
    for name in verification.FILES:
        (grader / instance_id / name).write_text("SECRET_GRADER_SENTINEL", encoding="utf-8")
    monkeypatch.setattr(verification, "MATERIALIZED_ROOT", materialized)
    monkeypatch.setattr(verification, "GRADER_ROOT", grader)
    monkeypatch.setattr(verification, "STAGING_ROOT", staging)
    monkeypatch.setattr(verification, "_image_digest", lambda image: "repo@sha256:" + "a" * 64)
    monkeypatch.setattr(
        verification,
        "_phase",
        lambda instance_id, phase, timeout: {
            "phase": phase,
            "phase_pass": True,
            "timeout": False,
            "private_detail": "SECRET_GRADER_SENTINEL",
        },
    )
    result = verification.verify_task(instance_id, "image:latest")
    serialized = (materialized / instance_id / "verification.json").read_text(encoding="utf-8")
    assert result["base_fail"] is True
    assert result["gold_pass"] is True
    assert "SECRET_GRADER_SENTINEL" not in serialized
    assert "private_detail" not in serialized
