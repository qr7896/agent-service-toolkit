import ast
import hashlib
import io
import runpy
import subprocess
import sys
from types import SimpleNamespace

import pytest

from evals import e1c_evaluation_2_object_observer as observer

RAW = b'class Api:\n    def __init__(self):\n        pass\n'
SHA = hashlib.sha256(RAW).hexdigest()
SITE = {'path': 'core.py', 'line': 2, 'variable': 'self', 'source_sha256': SHA}
BINDING = {'path': 'core.py', 'line': 2, 'symbol': 'Api'}
EXPORT = {'path': 'core.py', 'source_sha256': SHA}


def driver():
    return observer.build_driver('a' * 64, [SITE], 'b' * 32, [BINDING], [EXPORT], 'c' * 40)


def test_driver_only_observes_identity_and_preserves_canonical_checks():
    source, _ = driver()
    ast.parse(source)
    assert 'live != canonical' in source and 'subprocess.check_output' in source
    assert 'type.__dict__' in source and 'c is declared' in source
    assert 'semantic_alignment_proven' in source and 'repr(' not in source and 'getattr(' not in source


@pytest.mark.parametrize('kind', ['exact', 'subclass', 'impostor', 'missing'])
def test_values_free_runtime_type_binding_cases(monkeypatch, kind):
    source, _ = driver()
    monkeypatch.setattr(subprocess, 'check_output', lambda *args: RAW)
    monkeypatch.setattr(runpy, 'run_path', lambda *args, **kwargs: None)
    monkeypatch.setattr(sys, 'settrace', lambda *args: None)
    # Only the synthetic driver body is exercised; no repository code or Docker.
    data = {'probe_sha256': SHA, 'base_commit': 'c' * 40, 'marker': 'synthetic=',
            'bindings': [BINDING], 'export_sources': [EXPORT]}
    namespace = {'DATA': data, 'open': lambda *args: io.BytesIO(RAW)}
    exec(observer.DRIVER, namespace)

    class Api:
        def __repr__(self):
            raise AssertionError('repr must not run')

        def __getattribute__(self, name):
            raise AssertionError('instance attributes must not be read')

    class Child(Api):
        pass

    class Other:
        pass

    obj = Child() if kind == 'subclass' else Other() if kind == 'impostor' else Api()
    frame = SimpleNamespace(f_code=SimpleNamespace(co_filename='/testbed/core.py', co_firstlineno=2, co_name='__init__'),
                            f_locals={} if kind == 'missing' else {'self': obj}, f_globals={'Api': Api})
    namespace['trace'](frame, 'call', None)
    row = namespace['records'][0]
    assert row['instance_type_is_declared_class'] is (kind == 'exact')
    assert row['declared_class_in_instance_mro'] is (kind in {'exact', 'subclass'})
    assert set(row) == {'path', 'line', 'symbol', 'self_present', 'declared_class_present',
                        'instance_type_is_declared_class', 'declared_class_in_instance_mro'}


@pytest.mark.parametrize('binding,exports', [({**BINDING, 'line': 3}, [EXPORT]),
                                            ({**BINDING, 'symbol': '__class__'}, [EXPORT]),
                                            (BINDING, [{**EXPORT, 'source_sha256': 'd' * 64}]),
                                            (BINDING, [EXPORT, EXPORT])])
def test_wrong_site_symbol_hash_or_duplicate_sources_rejected(binding, exports):
    with pytest.raises(ValueError):
        observer.build_driver('a' * 64, [SITE], 'b' * 32, [binding], exports, 'c' * 40)


def test_constructor_selection_derived_from_chain_and_unchanged_host(tmp_path):
    (tmp_path / 'core.py').write_bytes(RAW)
    rows = [{'status': 'static_chain_supported', 'chain': [{'qualified': 'core.Api', 'path': 'core.py',
             'host_sha256': SHA, 'canonical_sha256': SHA}]}]
    bindings, exports, unknown = observer.constructor_bindings(rows, tmp_path)
    assert bindings == [BINDING] and exports == [EXPORT] and not unknown
    (tmp_path / 'core.py').write_bytes(RAW + b'# changed\n')
    with pytest.raises(ValueError, match='source changed'):
        observer.constructor_bindings(rows, tmp_path)
