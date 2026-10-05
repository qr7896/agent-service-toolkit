from evals import e1c_evaluation_2_counterfactual_dev as study


def test_failed_derived_control_is_terminal_not_a_fallback(tmp_path, monkeypatch):
    payload = {"target_action": "api()"}
    monkeypatch.setattr(study, "compile_pair", lambda *args: (payload, {"compiled": True, "target_program_changed": False}))
    calls = []

    def execute(*args):
        calls.append(args[1])
        return {"status": "fixture_or_positive_control_failed", "control_pass": False}

    monkeypatch.setattr(study, "_execute", execute)
    result = study.execute_role("B", payload, {}, tmp_path, "fixture", tmp_path / "B", {})
    assert result["status"] == "fixture_contract_rejected"
    assert calls == [payload]
    assert not study.should_fallback(result)
    assert (tmp_path / "B/counterfactual_control.json").exists()


def test_unknown_pair_is_not_reported_verified(tmp_path, monkeypatch):
    payload = {"target_action": "api()"}
    monkeypatch.setattr(study, "compile_pair", lambda *args: (payload, {"compiled": False, "status": "unsupported_or_unproven_pair"}))
    expected = {"status": "fixture_or_positive_control_failed", "control_pass": False}
    monkeypatch.setattr(study, "_execute", lambda *args: expected)
    result = study.execute_role("B", payload, {}, tmp_path, "fixture", tmp_path / "B", {})
    assert result == expected
    assert study.should_fallback(result)
