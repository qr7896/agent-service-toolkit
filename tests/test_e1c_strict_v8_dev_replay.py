from pathlib import Path

from evals.e1c_strict_v8_dev_replay import build


def test_v8_dev_replay_never_counts_as_independent(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("evals.e1c_strict_v8_dev_replay._v6_rows", lambda: [
        {"candidate_count": 1, "executable_candidate_count": 1, "source_results": [{"result": {"passed": False}}]}
    ])
    monkeypatch.setattr("evals.e1c_strict_v8_dev_replay._v7_rows", lambda: [
        {"candidate_count": 0, "executable_candidate_count": 0, "source_results": []}
    ])
    value = build()
    assert value["independent_evidence"] is False
    assert value["may_open_c5"] is False
    assert value["may_open_dev30"] is False
    assert value["may_open_fresh30"] is False
    assert value["source_base_fail_task_count"] == 1
