from evals.e1b_v8_offline_preflight import preflight


def test_v8_preflight_is_zero_call_and_does_not_authorize_live():
    report = preflight()
    assert report["provider_calls"] == 0
    assert report["tasks"] == 4
    assert report["schema_valid"] is True
    assert report["live_authorized"] is False
    assert all(row["schema_version"] == "e1b-state-transition-v1" for row in report["rows"])
    if report["result_exists"] or report["ledger_exists"]:
        assert report["ready_for_runner_freeze"] is False
    else:
        assert report["ready_for_runner_freeze"] is True
