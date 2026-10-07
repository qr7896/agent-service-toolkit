import ast

import pytest

from evals.e1c_evaluation_2_parameter_contract import (
    compare_documented_type,
    parameter_declarations,
)


def test_only_requested_parameter_headers_not_examples_returns_or_assertions():
    source = 'def api():\n    """Summary.\n\n    Parameters\n    ----------\n    labels : list of str, default=None\n        Public input.\n    count : int, default=10\n\n    Returns\n    -------\n    labels : int\n\n    Examples\n    --------\n    assert output == 17\n    labels : float\n    """\n    pass\n'
    rows = parameter_declarations(ast.parse(source).body[0], ['labels', 'count'])
    assert [r['declaration'] for r in rows] == ['list of str, default=None', 'int, default=10']
    for row in rows:
        assert row['parameter'] + ' :' in source.splitlines()[row['source_line'] - 1]
    assert 'assert' not in str(rows) and 'output' not in str(rows)


@pytest.mark.parametrize('declaration,observed,expected', [
    ('list of str, default=None', 'numpy.ndarray', 'observed_type_not_explicitly_documented'),
    ('list of str, default=None', 'list', 'documented_container_kind_supported_elements_unproven'),
    ('int, default=10', 'int', 'documented_type_supported'),
    ('array-like of shape (n_features,)', 'numpy.ndarray', 'unknown_documentation_grammar'),
])
def test_positive_vocabulary_is_not_universal_semantic_denial(declaration, observed, expected):
    assert compare_documented_type(declaration, observed) == expected


def test_no_parameter_section_does_not_invent_source_contract():
    node = ast.parse('def api():\n    """Examples\n    --------\n    count : int\n    """\n    pass\n').body[0]
    assert parameter_declarations(node, ['count']) == []
