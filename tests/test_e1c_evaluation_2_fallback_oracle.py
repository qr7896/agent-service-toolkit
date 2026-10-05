from evals.e1c_evaluation_2_fallback_oracle import compile_fallback


def contract():
    return {"issue_quote": "the public API call should complete", "expected_quote": "API call should complete",
            "oracle": "call_completes", "setup_source": "", "control_action": "api(0)", "target_action": "api(1)", "assertion": ""}


def test_fallback_cannot_invent_return_value_when_contract_is_completion_only():
    source = "from pkg import api\nresult = api(1)\nassert result == 42\n"
    result, proof = compile_fallback(source, contract(), {"issue": "the public API call should complete"})
    assert "result = api(1)" in result and "== 42" not in result
    assert "assert _e1c_fallback_done" in result
    assert proof["compiled"] and proof["api_program_changed"] is False


def test_no_rewrite_for_unrelated_call_or_ungrounded_contract():
    source = "result = other_api(1)\nassert result == 42\n"
    assert compile_fallback(source, contract(), {"issue": "the public API call should complete"})[0] == source
    assert compile_fallback(source, {**contract(), "expected_quote": "invented relation"}, {"issue": "the public API call should complete"})[0] == source
