import json

import pytest

from evals import e1c_evaluation_2_unified_codec_dev as runner

ISSUE = "A public API should complete.\nThe documented API accepts this input.\n"
PAYLOAD = {"issue_quote_ref": 0, "expected_quote_ref": 1, "oracle": "call_completes",
           "setup_source": "from core import api", "control_action": "api(1)", "target_action": "api(2)", "assertion": ""}


@pytest.mark.parametrize("tag", [{"type": "probe"}, {"action": "probe"}, {"type": "json_object", "action": "probe"}])
def test_exact_supported_variants_preserve_code_and_quote_refs(tag):
    action, payload, proof = runner.decode(json.dumps({**tag, **PAYLOAD}), ISSUE)
    assert action == "probe" and payload["target_action"] == PAYLOAD["target_action"]
    assert payload["issue_quote"] == ISSUE.splitlines(keepends=True)[0]
    assert proof["known_typed_ref_shape_only"]


@pytest.mark.parametrize("extra", [{"action": "shell"}, {"type": "unknown"}, {"type": "probe", "shell": "pytest"}])
def test_unknown_or_extra_action_variants_still_rejected(extra):
    with pytest.raises(ValueError):
        runner.decode(json.dumps({**extra, **PAYLOAD}), ISSUE)


def test_scoped_codec_restores_legacy_and_budget():
    old = runner.base._ready.decode
    with runner.configured():
        assert runner.base._ready.decode is runner.decode
        assert runner.base._compiled.CAP == 50000 and runner.base._compiled.TASK_CAP == 24000
    assert runner.base._ready.decode is old
