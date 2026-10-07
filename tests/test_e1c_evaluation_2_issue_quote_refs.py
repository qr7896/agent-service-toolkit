import json

import pytest

from evals import e1c_evaluation_2_referenced_runtime_dev as runner
from evals.e1c_evaluation_2_issue_quote_refs import catalogue, resolve

ISSUE = "Reported API input fails.\nThe documented input should complete.\n"


def payload(**extra):
    return {"issue_quote_ref": 0, "expected_quote_ref": 1, "oracle": "call_completes", "setup_source": "from core import api",
            "control_action": "api(1)", "target_action": "api(2)", "assertion": "", **extra}


@pytest.mark.parametrize("issue", [ISSUE, "\r\n中文真实issue行\r\n", "a" * 3001 + "\n", ""])
def test_catalogue_is_lossless_and_each_bound_is_original(issue):
    rows = catalogue(issue)["spans"]
    assert "".join(row["text"] for row in rows) == issue
    assert all(issue[r["start"]:r["end"]] == r["text"] for r in rows)
    assert all(len(r["text"]) <= 1400 for r in rows)


def test_resolve_never_invents_or_selects_expected_values():
    canonical, proof = resolve(payload(), ISSUE)
    assert canonical["issue_quote"] == ISSUE.splitlines(keepends=True)[0]
    assert canonical["expected_quote"] == ISSUE.splitlines(keepends=True)[1]
    assert canonical["target_action"] == payload()["target_action"]
    assert not proof["quote_text_invented"] and not proof["semantic_alignment_proven"]


@pytest.mark.parametrize("bad", [-1, 2, True, "1", 1.0])
def test_unknown_noninteger_reference_is_rejected(bad):
    with pytest.raises(ValueError, match="invalid_public"):
        resolve(payload(expected_quote_ref=bad), ISSUE)


def test_short_span_and_extra_fields_cannot_bypass_reference_schema():
    with pytest.raises(ValueError):
        resolve(payload(), "Tiny\nShould complete.\n")
    with pytest.raises(ValueError):
        resolve(payload(shell="pytest"), ISSUE)


def test_runtime_reference_binding_and_identity_restoration():
    original = runner.compiled.messages
    with runner.configured():
        msgs = runner.compiled.messages({"issue": ISSUE, "windows": []})
        body = json.loads(msgs[1].content)
        assert "issue" not in body and "".join(r["text"] for r in body["public_issue_catalogue"]["spans"]) == ISSUE
        action, canonical = runner.compiled.parse_action(json.dumps({"type": "json_object", "probe": payload()}))
        assert action == "probe" and canonical["expected_quote"] in ISSUE
    assert runner.compiled.messages is original and runner._issue.get() is None
