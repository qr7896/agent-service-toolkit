from evals.e1c_strict_v5_admission_seal import seal


def test_seal_blocks_live_when_two_or_more_frozen_rows_have_no_reproducer(
    tmp_path, monkeypatch
) -> None:
    report = {
        "ready": False,
        "reason": "strict_v5_admission_incomplete",
        "trusted_reproducer_count": 0,
        "minimum_trusted_reproducers": 2,
        "frozen_instance_ids": ["a", "b", "c"],
        "checks": {
            "identity_frozen": True,
            "projection_supported": True,
            "source_identity": True,
            "official_image": True,
            "base_fail": True,
            "gold_pass": True,
            "leakage_free": True,
            "infrastructure_ok": True,
            "trusted_reproducer_minimum": False,
        },
        "evidence_rows": [
            {"probe_status": "no_reproducer"},
            {"probe_status": "no_reproducer"},
            {"probe_status": "candidate_executable_probes"},
        ],
    }
    monkeypatch.setattr(
        "evals.e1c_strict_v5_admission_seal.build",
        lambda: report,
    )
    report_file = tmp_path / "report.json"
    report_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "evals.e1c_strict_v5_admission_seal.REPORT",
        report_file,
    )
    result = seal(tmp_path / "seal.json")
    assert result["live_allowed"] is False
    assert result["decisive_pre_live_failure"] is True
    assert result["same_canary_reuse_for_mechanism_tuning_allowed"] is False


def test_seal_does_not_call_no_reproducer_decisive_before_infra_and_grading_complete(
    tmp_path, monkeypatch
) -> None:
    report = {
        "ready": False,
        "reason": "strict_v5_admission_incomplete",
        "trusted_reproducer_count": 0,
        "minimum_trusted_reproducers": 2,
        "frozen_instance_ids": ["a", "b", "c"],
        "checks": {
            "identity_frozen": True,
            "projection_supported": True,
            "source_identity": True,
            "official_image": False,
            "base_fail": False,
            "gold_pass": False,
            "leakage_free": True,
            "infrastructure_ok": False,
            "trusted_reproducer_minimum": False,
        },
        "evidence_rows": [
            {"probe_status": "no_reproducer"},
            {"probe_status": "no_reproducer"},
            {"probe_status": "no_reproducer"},
        ],
    }
    monkeypatch.setattr("evals.e1c_strict_v5_admission_seal.build", lambda: report)
    report_file = tmp_path / "report.json"
    report_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr("evals.e1c_strict_v5_admission_seal.REPORT", report_file)
    result = seal(tmp_path / "seal.json")
    assert result["decisive_pre_live_failure"] is False
    assert result["admission_prerequisites_complete"] is False
    assert result["reason"] == "admission_prerequisites_incomplete"
