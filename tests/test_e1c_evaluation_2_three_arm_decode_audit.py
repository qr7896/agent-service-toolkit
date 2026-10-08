import json

import pytest

from evals.e1c_evaluation_2_three_arm_decode_audit import canonical_response


@pytest.mark.parametrize('wrapped', [False, True])
def test_exact_envelope_normalization_preserves_all_edit_strings(wrapped):
    edits = [{'path': 'src/module.py', 'old': 'old\n文字', 'new': 'new\n文字'}]
    raw = {'edits': edits}
    if wrapped:
        raw['type'] = 'json_object'
    normalized, removed = canonical_response(json.dumps(raw))
    assert json.loads(normalized) == {'edits': edits}
    assert removed is wrapped


@pytest.mark.parametrize('value', [[], None, {'edits': [], 'type': 'other'},
                                  {'edits': [], 'instructions': 'run'},
                                  {'edits': [], 'type': 'json_object', 'extra': 'forbidden'}])
def test_unknown_envelopes_and_extra_fields_are_still_rejected(value):
    with pytest.raises(ValueError):
        canonical_response(json.dumps(value))
