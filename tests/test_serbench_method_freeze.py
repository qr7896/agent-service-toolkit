from evals.serbench_method_freeze import freeze


def test_fail_closed_unverified(tmp_path):
    p = tmp_path / "p"
    r = tmp_path / "r"
    p.write_text("x")
    r.write_text("y")
    assert not freeze(p, r, "m", "cal500", "UNVERIFIED")["test500_allowed"]


def test_complete_freeze_allows_test500(tmp_path):
    p = tmp_path / "p"
    r = tmp_path / "r"
    c = tmp_path / "c"
    p.write_text("x")
    r.write_text("y")
    c.write_text(
        '{"method":"m","action_space":[],"ranking_budget":8,"stop_rule":{},'
        '"filter_v3":{},"evidence_features":[],"prediction_protocol":{},'
        '"implementation_files":[]}'
    )
    result = freeze(p, r, "m", "cal500", "a" * 40, c)
    assert result["test500_allowed"]
