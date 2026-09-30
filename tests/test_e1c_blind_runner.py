import json
from pathlib import Path

import pytest

from evals.e1c_blind_boundary import BlindBoundaryViolation, audit_serialized_agent_trace
from evals.e1c_blind_runner import SYSTEM, blind_payload


def _workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "repo"
    (workspace / "pkg").mkdir(parents=True)
    (workspace / "pkg" / "parser.py").write_text(
        "def parse_value(value):\n    return value.strip()\n", encoding="utf-8"
    )
    return workspace


def test_system_has_no_oracle_language() -> None:
    audit_serialized_agent_trace(SYSTEM)


def test_blind_payload_uses_only_issue_and_exact_base(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    monkeypatch.setattr("evals.e1c_blind_runner._statement", lambda _: "parse_value should preserve empty values")
    row = {"instance_id": "repo__issue-1", "base_commit": "a" * 40}
    payload = blind_payload(row, workspace, structured=True)
    assert payload["evidence_mode"] == "issue_structured_locator"
    assert payload["excerpts"]
    assert all(item["origin"] == "issue+exact_base" for item in payload["excerpts"])
    assert all((workspace / item["path"]).is_file() for item in payload["excerpts"])
    assert "instance_id" not in payload
    audit_serialized_agent_trace(json.dumps(payload))


@pytest.mark.parametrize(
    "text",
    [
        '{"FAIL_TO_PASS":["hidden"]}',
        '{"note":"test.patch"}',
        '{"candidate_patch":"old"}',
        '{"official_grade":true}',
    ],
)
def test_repair_trace_rejects_oracle_sentinels(text: str) -> None:
    with pytest.raises(BlindBoundaryViolation):
        audit_serialized_agent_trace(text)
