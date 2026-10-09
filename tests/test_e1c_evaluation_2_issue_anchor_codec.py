import json

import pytest

from evals import e1c_evaluation_2_issue_anchor_codec as codec


def test_precall_registry_is_deterministic_bounded_and_has_exact_spans():
    issue = '\n tiny \n  中文public behavior  \n' + '\n'.join('long ' * 100 for _ in range(20))
    value = codec.anchors(issue)
    assert value == codec.anchors(issue) and len(value['records']) == 12
    assert all(issue[r['start']:r['end']] == r['text'] and len(r['text']) <= 300 for r in value['records'])


def test_registered_id_projection_preserves_program_strings_and_passes_existing_codec():
    from evals.e1c_evaluation_2_pair_dev_v2 import validate_pair

    issue = 'The public issue requires consistent behavior.'
    registry = codec.anchors(issue)
    value = {'normal_source': 'from module import api\nassert api(1) == 2\n',
             'target_source': 'from module import api\nassert api(2) == 3\n', 'issue_anchor_id': registry['records'][0]['id']}
    raw = codec.decode_pair(json.dumps(value), issue, registry)
    decoded = json.loads(raw)
    assert decoded['normal_source'] == value['normal_source'] and decoded['target_source'] == value['target_source']
    assert decoded['issue_quote'] == issue
    candidates = validate_pair(raw, {'issue': issue, 'input_sha256': 'a' * 64, 'candidate_paths': ['module.py']}, None)
    assert candidates['target']['source'] == value['target_source']


@pytest.mark.parametrize('change', ['unknown_id', 'changed_registry', 'extra_key'])
def test_invalid_anchor_or_schema_rejected_without_posthoc_quote_repair(change):
    issue = 'The public issue requires consistent behavior.'
    registry = codec.anchors(issue)
    value = {'normal_source': 'normal', 'target_source': 'target', 'issue_anchor_id': registry['records'][0]['id']}
    if change == 'unknown_id':
        value['issue_anchor_id'] = 'invented'
    elif change == 'changed_registry':
        registry['records'][0]['text'] = 'invented quote'
    else:
        value['issue_quote'] = 'hand corrected'
    with pytest.raises(ValueError):
        codec.decode_pair(json.dumps(value), issue, registry)
