from evals.e1c_swebench_curator import curate


def test_curate_is_deterministic_and_filters_invalid_rows():
    rows = [
        {"instance_id": "b", "repo": "r/b", "base_commit": "2", "FAIL_TO_PASS": "[1]", "PASS_TO_PASS": "[2]"},
        {"instance_id": "a", "repo": "r/a", "base_commit": "1", "FAIL_TO_PASS": "[1]", "PASS_TO_PASS": "[2]"},
        {"instance_id": "bad", "repo": "r/c", "base_commit": "3", "FAIL_TO_PASS": "[]", "PASS_TO_PASS": "[2]"},
    ]
    first = curate(rows, 2)
    second = curate(list(reversed(rows)), 2)
    assert first == second
    assert first["admitted_metadata_candidates"] == 2
