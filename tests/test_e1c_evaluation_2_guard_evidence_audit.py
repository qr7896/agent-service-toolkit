import hashlib

import pytest

from evals.e1c_evaluation_2_guard_evidence_audit import guard_evidence


def context(tmp_path):
    source = "def api(values):\n    if values is not None:\n        pass\n" + "\n" * 80 + "    if values:\n        return True\n    return False\n"
    (tmp_path / "core.py").write_bytes(source.encode())
    return {"issue": "Reported traceback in api:\nif values:\n", "candidate_paths": ["core.py"],
            "windows": [{"path": "core.py", "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                         "start_line": 1, "end_line": 3, "text": "def api(values):\n    if values is not None:\n        pass"}]}


def test_public_failed_condition_locates_guard_beyond_definition_window(tmp_path):
    frozen = context(tmp_path)
    result = guard_evidence({"setup_source": "from core import api as call", "target_action": "call(values)", "issue_quote": "production api failure"}, frozen, tmp_path)
    assert result["provider_calls"] == 0 and len(result["rows"]) == 2
    first = result["rows"][0]
    assert first["predicate"] == "values" and first["matches_public_failure_condition"]
    assert not first["already_visible"] and "if values:" in first["window"]["text"]
    assert first["relation_type"] == "guard" and first["depth"] == 1
    assert not result["live_integrated"] and not result["semantic_alignment_proven"]


def test_unknown_API_does_not_guess_another_definition(tmp_path):
    result = guard_evidence({"setup_source": "from core import missing", "target_action": "missing(values)", "issue_quote": "unknown API"}, context(tmp_path), tmp_path)
    assert result["rows"] == []


def test_protected_or_changed_sources_not_read_as_evidence(tmp_path):
    frozen = context(tmp_path)
    frozen["windows"][0]["source_sha256"] = "changed"
    with pytest.raises(ValueError):
        guard_evidence({"setup_source": "from core import api", "target_action": "api(values)", "issue_quote": "public API"}, frozen, tmp_path)
    frozen = context(tmp_path)
    frozen["candidate_paths"] = ["tests/answer.py"]
    with pytest.raises(Exception):
        guard_evidence({"setup_source": "from core import api", "target_action": "api(values)", "issue_quote": "public API"}, frozen, tmp_path)
