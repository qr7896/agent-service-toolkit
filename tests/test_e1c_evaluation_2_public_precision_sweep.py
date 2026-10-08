import ast

import pytest

from evals.e1c_evaluation_2_public_precision_sweep import release_identity, variants


def test_variants_are_derived_from_one_public_literal_without_changing_calls_or_oracle():
    anchor = '2019-06-17T00:57:41.000Z'
    original = f"value = {anchor!r}\nresult = library.load(value)\nassert result\n"
    chosen, rows = variants(original, 'Public issue: ' + anchor)
    assert chosen == anchor and len(rows) == 21
    assert {r['precision'] for r in rows} == set(range(7))
    assert {r['zone'] for r in rows} == {'Z', '+00:00', '-04:30'}
    assert len({r['source'] for r in rows}) == 21
    for row in rows:
        tree = ast.parse(row['source'])
        assert ast.dump(tree.body[1]) == ast.dump(ast.parse(original).body[1])
        assert ast.dump(tree.body[2]) == ast.dump(ast.parse(original).body[2])
    assert sum(not r['synthetic_variant_not_reported_literal'] for r in rows) == 1


@pytest.mark.parametrize('source,issue', [("x='not a timestamp'", 'public'),
                                        ("x='2019-06-17T00:57:41.000Z'", 'no public anchor'),
                                        ("x='2019-06-17T00:57:41.000Z'\ny='2019-06-18T00:57:41.000Z'", '2019-06-17T00:57:41.000Z 2019-06-18T00:57:41.000Z')])
def test_missing_ambiguous_or_nonpublic_anchor_is_rejected(source, issue):
    with pytest.raises(ValueError, match='one ISO literal'):
        variants(source, issue)


def test_release_identity_uses_actual_separate_freeze_and_receipt_fields():
    freeze = {'wheel_sha256': 'wheel', 'sources': [{'path': 'module/utils.py', 'sha256': 'source'}]}
    result = {'version': 'old'}
    receipt = {'wheel_sha256': 'wheel', 'module': 'module', 'version': 'old'}
    joined = release_identity(freeze, result, receipt)
    assert joined['module'] == 'module' and joined['version'] == 'old'
    assert 'module' not in freeze
    with pytest.raises(ValueError, match='disagree'):
        release_identity(freeze, result, {**receipt, 'version': 'different'})
