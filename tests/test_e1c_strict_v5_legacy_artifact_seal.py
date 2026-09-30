import evals.e1c_strict_v5_legacy_artifact_seal as seal


def test_build_and_verify_legacy_seal(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(seal, "ROOT", tmp_path)
    monkeypatch.setattr(seal, "LEGACY_PATHS", ("a.json", "b.jsonl"))
    (tmp_path / "a.json").write_text("{}", encoding="utf-8")
    (tmp_path / "b.jsonl").write_text('{"x":1}\n', encoding="utf-8")
    path = tmp_path / "seal.json"
    result = seal.build(path)
    assert result["ready"] is True
    assert result["sealed_file_count"] == 2
    assert result["legacy_results_authoritative_for_v5"] is False
    assert seal.verify(path)["match"] is True


def test_verify_fails_on_legacy_artifact_mutation(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(seal, "ROOT", tmp_path)
    monkeypatch.setattr(seal, "LEGACY_PATHS", ("a.json",))
    artifact = tmp_path / "a.json"
    artifact.write_text("old", encoding="utf-8")
    path = tmp_path / "seal.json"
    seal.build(path)
    artifact.write_text("new", encoding="utf-8")
    result = seal.verify(path)
    assert result["match"] is False
    assert result["changed_paths"] == ["a.json"]


def test_build_fails_closed_when_expected_legacy_artifact_missing(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(seal, "ROOT", tmp_path)
    monkeypatch.setattr(seal, "LEGACY_PATHS", ("missing.json",))
    result = seal.build(tmp_path / "seal.json")
    assert result["ready"] is False
    assert result["reason"] == "legacy_artifacts_missing"
    assert result["missing_paths"] == ["missing.json"]


def test_seal_sha_depends_on_paths_and_hashes_not_sizes() -> None:
    one = [{"path": "a", "sha256": "a" * 64, "size_bytes": 1}]
    two = [{"path": "a", "sha256": "a" * 64, "size_bytes": 999}]
    assert seal._seal_sha(one) == seal._seal_sha(two)
