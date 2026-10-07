import ast

import pytest

from evals import e1c_evaluation_2_exception_observer as observer

SITE = {"path": "core.py", "line": 3, "variable": "exception", "source_sha256": "a" * 64}


def test_constant_driver_hashes_real_builtin_messages_without_values_or_certificate():
    source, marker = observer.build_driver("b" * 64, [SITE], "c" * 32, ["d" * 64], ["flag"])
    ast.parse(source)
    assert "event == 'exception'" in source and marker in source
    assert "raw_messages_emitted': False" in source and "semantic_alignment_proven': False" in source
    assert "repr(" not in source and "getattr(" not in source and "sys.settrace(None)" in source


def test_public_message_hashes_limited_to_reported_failure_clauses():
    hashes = observer.public_message_hashes("AttributeError: a public missing member\nIt is failing with a `public parser error`.\n`ordinary_api`\n")
    assert len(hashes) == 2 and all(len(h) == 64 for h in hashes)


@pytest.mark.parametrize("hashes,keywords", [(["not-a-digest"], []), ([], ["__dict__"]), (["a" * 64] * 9, [])])
def test_unknown_or_expanded_capabilities_rejected(hashes, keywords):
    with pytest.raises(ValueError):
        observer.build_driver("b" * 64, [SITE], "c" * 32, hashes, keywords)


def test_wrapper_preserves_optional_environment_and_restores_transport(monkeypatch):
    before = observer.transport.build_driver, observer.transport.docker_command
    captured = []
    monkeypatch.setattr(observer, "_docker_command", lambda *a, **k: captured.append(k) or [])
    monkeypatch.setattr(observer.transport, "observe", lambda *a: observer.transport.docker_command({}, "image", "base", "probe"))
    observer.observe({}, "probe", [SITE], "image", "base", "root", public_hashes=[], keywords=[], blocked_import_dir="same-environment")
    assert captured == [{"blocked_import_dir": "same-environment"}]
    assert (observer.transport.build_driver, observer.transport.docker_command) == before
