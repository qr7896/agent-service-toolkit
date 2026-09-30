import pytest

from evals.e1c_evaluation_2_fenced_response_replay import parse_fenced_source


def test_only_outer_json_fence_is_removed():
    assert parse_fenced_source('```json\n{"source":"assert True"}\n```') == "assert True"
    with pytest.raises(ValueError, match="one JSON code fence"):
        parse_fenced_source('prefix ```json\n{"source":"assert True"}\n```')
