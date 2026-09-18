from evals.e1_smoke import classify_failure, file_diagnostics, summarize


class Spec:
    gold_sources = {"a.py": "x", "b.py": "y"}


def g(resolved=False, f2p=True, p2p=True):
    return {"resolved": resolved, "fail_to_pass": {"f": f2p}, "pass_to_pass": {"p": p2p}}


def test_file_diagnostics():
    d = file_diagnostics(Spec(), {"a.py", "noise.py"})
    assert d["missing_gold_files"] == ["b.py"]
    assert d["irrelevant_files"] == ["noise.py"]
    assert d["irrelevant_read_ratio"] == 0.5


def test_failure_taxonomy():
    assert classify_failure(g(True), g(True), [], ["a.py"]) == "invalid_base"
    assert classify_failure(g(), g(True), ["b.py"], ["a.py"]) == "resolved"
    assert classify_failure(g(), g(), ["b.py"], ["a.py"]) == "retrieval_blocked"
    assert classify_failure(g(), g(False, False, True), [], ["a.py"]) == "patch_failure"
    assert classify_failure(g(), g(False, True, False), [], ["a.py"]) == "regression_failure"


def test_summary_oracle_name():
    r = {
        "policy": "p",
        "resolved": True,
        "tool_calls": 1,
        "context_tokens": 10,
        "retrieved_files_count": 1,
        "irrelevant_read_ratio": 0.0,
        "failure_type": "resolved",
    }
    s = summarize([r], "p")
    assert s["oracle_pass_at_1"] == 1.0
    assert "patch_success" not in s
