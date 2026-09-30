from evals.e1c_strict_v8_probe import candidate_plan


def test_v8_combines_v7_and_source_contract_candidates() -> None:
    localization = {"candidates": [{"path": "pkg/checks.py", "symbol": "check_alpha", "text": "def check_alpha(): pass"}]}
    plan = candidate_plan("check_alpha is never run?!", localization)
    assert plan["candidate_count"] == 1
    assert plan["executable_candidate_count"] == 1
    assert plan["status"] == "candidate_executable_witnesses"
