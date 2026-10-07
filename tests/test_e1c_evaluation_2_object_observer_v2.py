import ast
import hashlib

import pytest

from evals import e1c_evaluation_2_object_observer_v2 as observer


def test_indirect_runtime_base_relation_without_metaclass_unwrapping(tmp_path):
    raw = b'class Parent:\n    def __init__(self): pass\nclass Api(factory(Parent)):\n    pass\n'
    (tmp_path / 'core.py').write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    rows = [{'status': 'static_chain_supported', 'chain': [{'path': 'core.py', 'qualified': 'core.Api',
              'host_sha256': digest, 'canonical_sha256': digest}]}]
    bindings, exports, unknown = observer.constructor_bindings(rows, tmp_path)
    assert not unknown and bindings == [{'path': 'core.py', 'symbol': 'Api', 'line': 3, 'constructor_lines': [2]}]
    sites = [{'path': 'core.py', 'line': 3, 'variable': 'self', 'source_sha256': digest}]
    source, _ = observer.build_driver('a' * 64, sites, 'b' * 32, bindings, exports, 'c' * 40)
    ast.parse(source)
    assert "code.co_firstlineno in binding['constructor_lines']" in source
    assert "'declared_class_line': binding['line']" in source
    assert 'factory' not in source and 'with_metaclass' not in source


@pytest.mark.parametrize('lines', [[], [True], [-1], [200001], list(range(1, 34))])
def test_constructor_inventory_is_bounded_and_typed(lines):
    sites = [{'path': 'core.py', 'line': 3, 'variable': 'self', 'source_sha256': 'd' * 64}]
    bindings = [{'path': 'core.py', 'line': 3, 'symbol': 'Api', 'constructor_lines': lines}]
    with pytest.raises(ValueError):
        observer.build_driver('a' * 64, sites, 'b' * 32, bindings, [{'path': 'core.py', 'source_sha256': 'd' * 64}], 'c' * 40)


def test_decorated_or_cls_constructors_not_guessed(tmp_path):
    raw = b'class Api:\n    @wrap\n    def __init__(self): pass\nclass Other:\n    def __init__(cls): pass\n'
    (tmp_path / 'core.py').write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    _, _, unknown = observer.constructor_bindings([{'status': 'static_chain_supported', 'chain': [{
        'path': 'core.py', 'qualified': 'core.Api', 'host_sha256': digest, 'canonical_sha256': digest}]}], tmp_path)
    assert unknown == ['bounded_module_constructor_inventory_unknown']
