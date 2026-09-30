import json

import evals.e1c_strict_v5_resume_admission as resume


def test_resume_fails_closed_when_any_official_image_is_missing(tmp_path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "tasks": [
                    {"instance_id": "a__one", "image": "swebench/a:latest"},
                    {"instance_id": "b__two", "image": "swebench/b:latest"},
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(resume, "MANIFEST", manifest)
    monkeypatch.setattr(
        resume,
        "_local_digest",
        lambda image: "swebench/a@sha256:" + "a" * 64 if image.endswith("a:latest") else None,
    )
    monkeypatch.setattr(
        resume,
        "run_verification",
        lambda: (_ for _ in ()).throw(AssertionError("verification must not run")),
    )
    result = resume.run()
    assert result["ready"] is False
    assert result["reason"] == "frozen_official_images_missing"
    assert result["missing_instance_ids"] == ["b__two"]


def test_resume_runs_zero_provider_chain_when_all_images_exist(tmp_path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"tasks": [{"instance_id": "a__one", "image": "swebench/a:latest"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(resume, "MANIFEST", manifest)
    monkeypatch.setattr(resume, "_local_digest", lambda image: "swebench/a@sha256:" + "a" * 64)
    monkeypatch.setattr(resume, "run_verification", lambda: {"ready": True})
    monkeypatch.setattr(resume, "build_admission", lambda: {"ready": True})
    monkeypatch.setattr(
        resume,
        "build_seal",
        lambda: {"live_allowed": True, "reason": "strict_v5_admission_ready"},
    )
    result = resume.run()
    assert result["ready"] is True
    assert result["verification_ready"] is True
    assert result["admission_ready"] is True
    assert result["provider_calls"] == 0


def test_inspect_local_images_does_not_run_grader(tmp_path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"tasks": [{"instance_id": "a__one", "image": "swebench/a:latest"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(resume, "MANIFEST", manifest)
    monkeypatch.setattr(resume, "_local_digest", lambda image: None)
    monkeypatch.setattr(
        resume,
        "run_verification",
        lambda: (_ for _ in ()).throw(AssertionError("grader must not run")),
    )
    result = resume.inspect_local_images()
    assert result["ready"] is False
    assert result["missing_instance_ids"] == ["a__one"]
