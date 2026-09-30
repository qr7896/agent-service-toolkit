from pathlib import Path

import pytest

from evals.e1c_blind_boundary import (
    BlindBoundaryViolation,
    audit_forbidden_values,
    build_agent_view,
    read_agent_text,
)


def test_content_sentinel_is_rejected_even_without_oracle_filename() -> None:
    with pytest.raises(BlindBoundaryViolation):
        audit_forbidden_values('{"note":"SENTINEL-HIDDEN-ASSERTION"}', ["SENTINEL-HIDDEN-ASSERTION"])


def test_agent_view_read_rejects_escape(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "safe.py").write_text("x = 1\n", encoding="utf-8")
    outside = tmp_path / "outside.py"
    outside.write_text("secret\n", encoding="utf-8")
    view = build_agent_view(
        instance_id="repo__issue-1",
        problem_statement="fix safe",
        workspace=root,
    )
    assert read_agent_text(view, "safe.py") == "x = 1\n"
    with pytest.raises(BlindBoundaryViolation):
        read_agent_text(view, "../outside.py")
